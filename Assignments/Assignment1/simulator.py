import copy # Added for deepcopy
import pygame
import os
import sys
import re

TARGET_WINDOW_WIDTH = 1200
TARGET_WINDOW_HEIGHT = 800
IMAGE_SCALE_FACTOR = 0.7

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (210, 40, 40)
BLUE = (0, 0, 200)
GREEN_DARK = (0, 100, 0)

# --- TEST STATES ---
init_state = {
    "Size":  (8, 8),
    "Walls": {
        # All cells except the corridor (1,0), (1,1), (1,2)
        *( (r, c)
           for r in range(8)
           for c in range(8)
           if not (r == 1 and c in (0, 1, 2)) )
    },
    "Taps": {
        (1, 1): 3,
    },
    "Plants": {
        (1, 2): 3,
    },
    "Robots": {
        10: (1, 0, 0, 3),   # start left of tap, cap 3
    },
}
# --- ACTION LIST ---
# This list will complete the mission for the test state above
action_list = ['RIGHT{10}', 'LOAD{10}', 'LOAD{10}', 'RIGHT{10}', 'POUR{10}', 'POUR{10}', 'LEFT{10}', 'LOAD{10}', 'RIGHT{10}', 'POUR{10}']


# --- Helper Function ---
def get_object_at(state, r, c):
    if (r, c) in state.get("Walls", []):
        return "Wall"
    if (r, c) in state.get("Taps", {}):
        return "Tap"
    if (r, c) in state.get("Plants", {}):
        return "Plant"
    for robot_id, data in state.get("Robots", {}).items():
        if data[0] == r and data[1] == c:
            return "Robot"
    return "Empty"

# --- NEW: Function to Check for Win Condition ---
def check_mission_complete(state):
    """
    Returns True if all plants in the state have a value of 0 or less.
    """
    if not state.get("Plants"):
        return True # No plants to water, mission is "complete"

    for water_needed in state["Plants"].values():
        if water_needed > 0:
            return False # Found a plant that still needs water
    
    return True # All plants are at 0

# --- Action Handlers ---
def _handle_move(state, robot_id, action_type):
    GRID_ROWS, GRID_COLS = state["Size"]
    r, c, water, val2 = state["Robots"][robot_id]
    nr, nc = r, c
    if action_type == "UP":    nr -= 1
    if action_type == "DOWN":  nr += 1
    if action_type == "LEFT":  nc -= 1
    if action_type == "RIGHT": nc += 1

    if not (0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS):
        print(f"Action failed: {action_type} is out of bounds.")
        return False
        
    target_obj = get_object_at(state, nr, nc)
    if target_obj in ["Wall", "Robot"]:
        print(f"Action failed: {action_type} blocked by {target_obj}.")
        return False
        
    state["Robots"][robot_id] = (nr, nc, water, val2)
    print(f"Action successful: {action_type}")
    return True

def _handle_load(state, robot_id):
    r, c, water, val2 = state["Robots"][robot_id]
    if get_object_at(state, r, c) == "Tap":
        if water >= val2:
            print(f"Action failed: LOAD. Robot is at max capacity ({val2}).")
            return False
        tap_key = (r, c)
        tap_value = state["Taps"][tap_key]
        if tap_value > 0:
            state["Taps"][tap_key] -= 1
            state["Robots"][robot_id] = (r, c, water + 1, val2)
            print(f"Action successful: LOAD")
            return True
        else:
            print(f"Action failed: LOAD. Tap is empty.")
            return False
    else:
        print(f"Action failed: LOAD. Robot is not on a Tap.")
        return False

def _handle_pour(state, robot_id):
    r, c, water, val2 = state["Robots"][robot_id]
    if get_object_at(state, r, c) == "Plant":
        plant_key = (r, c)
        plant_value = state["Plants"][plant_key]
        
        if water <= 0:
            print(f"Action failed: POUR. Robot has no water.")
            return False
        if plant_value <= 0:
            print(f"Action failed: POUR. Plant needs no water.")
            return False
            
        state["Plants"][plant_key] -= 1
        state["Robots"][robot_id] = (r, c, water - 1, val2)
        print(f"Action successful: POUR")
        return True
    else:
        print(f"Action failed: POUR. Robot is not on a Plant.")
        return False

# --- State Management Function ---
def apply_action(state, action_string, config):
    match = re.match(r"(\w+)\{(\d+)\}", action_string)
    if not match:
        print(f"Invalid action string: {action_string}")
        return False

    action_type = match.group(1).upper()
    try:
        robot_id = int(match.group(2))
    except ValueError:
        print(f"Invalid robot ID: {match.group(2)}")
        return False
    
    if robot_id not in state["Robots"]:
        print(f"Action failed: Robot {robot_id} not found.")
        return False
        
    if action_type in ["UP", "DOWN", "LEFT", "RIGHT"]:
        return _handle_move(state, robot_id, action_type)
    elif action_type == "LOAD":
        return _handle_load(state, robot_id)
    elif action_type == "POUR":
        return _handle_pour(state, robot_id)
    else:
        print(f"Action failed: Unknown action type '{action_type}'")
        return False

def draw_element(screen, image, r, c, cell_size, config, text=None, text_color=BLACK, text_pos='center', sub_text=None, sub_text_color=BLUE):
    padding = config["padding"]
    cell_rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
    image_rect = image.get_rect(center=cell_rect.center)
    screen.blit(image, image_rect)
    
    if text is not None:
        text_surf = config["main_font"].render(str(text), True, text_color)
        if text_pos == 'center':
            text_rect = text_surf.get_rect(center=image_rect.center)
        elif text_pos == 'topright':
            text_rect = text_surf.get_rect(topright=(cell_rect.right - padding, cell_rect.top + padding))
        elif text_pos == 'bottomleft':
            text_rect = text_surf.get_rect(bottomleft=(cell_rect.left + padding, cell_rect.bottom - padding))
        screen.blit(text_surf, text_rect)
        
    if sub_text is not None:
        info_surf = config["small_font"].render(str(sub_text), True, sub_text_color)
        info_rect = info_surf.get_rect(topright=(cell_rect.right - padding, cell_rect.top + padding))
        screen.blit(info_surf, info_rect)

# --- Drawing Function (Updated) ---
def draw_game_state(screen, state, images, config, actions_taken_count, mission_complete):
    """
    Renders the entire game state, plus the action counter and complete screen.
    """
    screen.fill(WHITE)
    
    # Get all dynamic values from the config dict
    CELL_SIZE = config["CELL_SIZE"]
    main_font = config["main_font"]
    small_font = config["small_font"]
    large_font = config["large_font"]
    padding = config["padding"]
    line_thickness = config["line_thickness"]
    WINDOW_WIDTH = config["WINDOW_WIDTH"]
    WINDOW_HEIGHT = config["WINDOW_HEIGHT"]

    # --- Draw all game objects ---
    for (r, c) in state.get("Walls", []):
        draw_element(screen, images["wall"], r, c, CELL_SIZE, config)
        
    for (r, c), value in state.get("Taps", {}).items():
        draw_element(screen, images["tap"], r, c, CELL_SIZE, config, text=value)
        
    for (r, c), value in state.get("Plants", {}).items():
        draw_element(screen, images["plant"], r, c, CELL_SIZE, config, text=value, text_pos='topright')
        
    for robot_id, data in state.get("Robots", {}).items():
        r, c, water, val2 = data
        draw_element(screen, images["robot"], r, c, CELL_SIZE, config, 
                     text=robot_id, text_color=RED, text_pos='bottomleft',
                     sub_text=f"{water},{val2}", sub_text_color=BLUE)

    # --- Draw Grid Lines ---
    GRID_ROWS, GRID_COLS = state["Size"]
    for r in range(GRID_ROWS + 1):
        pygame.draw.line(screen, BLACK, (0, r * CELL_SIZE), (WINDOW_WIDTH, r * CELL_SIZE), line_thickness)
    for c in range(GRID_COLS + 1):
        pygame.draw.line(screen, BLACK, (c * CELL_SIZE, 0), (c * CELL_SIZE, WINDOW_HEIGHT), line_thickness)

    # --- NEW: Draw Action Counter ---
    # (Drawn last to be on top of the grid)
    count_text = f"Actions: {actions_taken_count}"
    count_surf = small_font.render(count_text, True, BLACK)
    # Create a small white background for it
    count_rect = count_surf.get_rect(topleft=(padding, padding))
    bg_rect = count_rect.inflate(padding // 2, padding // 2)
    pygame.draw.rect(screen, WHITE, bg_rect)
    screen.blit(count_surf, count_rect) # Draw the text on top of the white bg

    # --- NEW: Draw Mission Complete Overlay ---
    if mission_complete:
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 180)) # White, semi-transparent
        screen.blit(overlay, (0, 0))

        # Draw the text
        complete_text = "MISSION COMPLETE!"
        complete_surf = large_font.render(complete_text, True, GREEN_DARK)
        complete_rect = complete_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        screen.blit(complete_surf, complete_rect)

# --- Main Function (Updated) ---
def main(state_in=None, actions_in=None):
    pygame.init()
    pygame.font.init()

    if state_in is None:
        state_in = init_state
    if actions_in is None:
        actions_in = action_list
        
    # Deep copy to avoid modifying the original state if called multiple times
    init_state_copy = copy.deepcopy(state_in)

    try:
        GRID_ROWS, GRID_COLS = init_state_copy["Size"]
    except KeyError:
        print("Error: 'Size' key missing from init_state.")
        sys.exit()

    cell_size_w = TARGET_WINDOW_WIDTH // GRID_COLS
    cell_size_h = TARGET_WINDOW_HEIGHT // GRID_ROWS
    CELL_SIZE = min(cell_size_w, cell_size_h)
    WINDOW_WIDTH = GRID_COLS * CELL_SIZE
    WINDOW_HEIGHT = GRID_ROWS * CELL_SIZE
    DISPLAY_IMAGE_SIZE = int(CELL_SIZE * IMAGE_SCALE_FACTOR)
    
    # Font sizes
    main_font_size = int(CELL_SIZE * 0.22)
    small_font_size = int(CELL_SIZE * 0.16)
    large_font_size = int(CELL_SIZE * 0.3)  
    padding = int(CELL_SIZE * 0.08)
    line_thickness = max(1, int(CELL_SIZE * 0.01))
    
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Grid Renderer ({GRID_ROWS}x{GRID_COLS}) - Click to advance action")
    clock = pygame.time.Clock()
    
    # Load fonts
    try:
        main_font = pygame.font.SysFont('Arial', main_font_size, bold=True)
        small_font = pygame.font.SysFont('Arial', small_font_size, bold=True)
        large_font = pygame.font.SysFont('Arial', large_font_size, bold=True) # New font
    except:
        main_font = pygame.font.Font(None, main_font_size)
        small_font = pygame.font.Font(None, small_font_size)
        large_font = pygame.font.Font(None, large_font_size) # New font

    # Load images
    script_dir = os.path.dirname(os.path.abspath(__file__))
    IMG_DIR = os.path.join(script_dir, "objects_pics")
    try:
        plant_img = pygame.image.load(os.path.join(IMG_DIR, "plant.png")).convert_alpha()
        robot_img = pygame.image.load(os.path.join(IMG_DIR, "robot.png")).convert_alpha()
        tap_img = pygame.image.load(os.path.join(IMG_DIR, "tap.png")).convert_alpha()
        wall_img = pygame.image.load(os.path.join(IMG_DIR, "wall.png")).convert_alpha()
        img_size = (DISPLAY_IMAGE_SIZE, DISPLAY_IMAGE_SIZE)
        loaded_images = {
            "plant": pygame.transform.scale(plant_img, img_size),
            "robot": pygame.transform.scale(robot_img, img_size),
            "tap": pygame.transform.scale(tap_img, img_size),
            "wall": pygame.transform.scale(wall_img, img_size),
        }
    except Exception as e:
        print(f"--- ERROR Loading Images ---")
        print(f"Error: {e}")
        pygame.quit()
        sys.exit()

    # Bundle all dynamic sizes into a config dict
    config = {
        "CELL_SIZE": CELL_SIZE,
        "main_font": main_font,
        "small_font": small_font,
        "large_font": large_font, # New
        "padding": padding,
        "line_thickness": line_thickness,
        "WINDOW_WIDTH": WINDOW_WIDTH, # New
        "WINDOW_HEIGHT": WINDOW_HEIGHT # New
    }
    
    current_actions = list(actions_in)
    
    # --- NEW: State variables ---
    actions_taken_count = 0
    mission_complete = False
    # ---
    
    print("--- Starting simulation. Click on the window to advance. ---")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse click
                    # Only process actions if the mission is not complete
                    if current_actions and not mission_complete:
                        action_to_do = current_actions.pop(0)
                        
                        # Check if the action was successful
                        success = apply_action(init_state_copy, action_to_do, config)
                        
                        if success:
                            actions_taken_count += 1 # Only increment on success
                            
                            # Check for win condition
                            mission_complete = check_mission_complete(init_state_copy)
                            if mission_complete:
                                print("-----------------------------------------------")
                                print(f"--- MISSION COMPLETE in {actions_taken_count} actions! ---")
                                print("-----------------------------------------------")
                                
                    elif mission_complete:
                         print("Mission is already complete.")
                    else:
                        print("--- All actions complete. ---")

        # Update the drawing call to include new state variables
        draw_game_state(screen, init_state_copy, loaded_images, config, actions_taken_count, mission_complete)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    # sys.exit() # Removed to prevent killing the caller

if __name__ == "__main__":
    main()