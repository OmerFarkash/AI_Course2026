import time
import ex1
import search
import simulator


def run_problem(func, targs=(), kwargs=None):
    if kwargs is None:
        kwargs = {}
    result = (-3, "default")
    try:
        result = func(*targs, **kwargs)
    except Exception as e:
        result = (-3, e)
    return result


def run_and_visualize(problem, algorithm='gbfs'):
    """
    Run a single problem and visualize the solution with the simulator.
    
    Args:
        problem: Problem dictionary
        algorithm: 'astar' or 'gbfs' (default: 'astar')
    """
    try:
        p = ex1.create_watering_problem(problem)
    except Exception as e:
        print("Error creating problem:", e)
        return
    
    if algorithm == 'gbfs':
        result = run_problem((lambda p: search.greedy_best_first_graph_search(p, p.h_gbfs)), targs=[p])
    else:
        result = run_problem((lambda p: search.astar_search(p, p.h_astar)), targs=[p])
    
    if result and isinstance(result[0], search.Node):
        solve = result[0].path()[::-1]
        solution = [pi.action for pi in solve][1:]
        print(f"[{algorithm.upper()}] Solution found with {len(solution)} steps")
        print(f"Actions: {solution}")
        simulator.main(problem, solution)
    else:
        print(f"[{algorithm.upper()}] No solution found")


def solve_problems(problem, algorithm, optimal_len=None):
    try:
        p = ex1.create_watering_problem(problem)
    except Exception as e:
        print("Error creating problem:", e)
        return None

    if algorithm == "gbfs":
        result = run_problem((lambda p: search.greedy_best_first_graph_search(p, p.h_gbfs)), targs=[p])
    else:
        result = run_problem((lambda p: search.astar_search(p, p.h_astar)), targs=[p])

    if result and isinstance(result[0], search.Node):
        solve = result[0].path()[::-1]
        solution = [pi.action for pi in solve][1:]  # type: ignore
        steps = len(solution)
        
        if algorithm == "gbfs":
            print(f"[GBFS] solved with {steps} steps, optimal solution is {optimal_len} steps")
        else:
            # A* case
            if optimal_len is not None and optimal_len != -1:
                if steps > optimal_len:
                    print(f"[A*] solved with {steps} steps, optimal solution is {optimal_len} steps - SUBOPTIMAL!")
                    simulator.main(problem, solution)
                else:
                    print(f"[A*] solved with {steps} steps, optimal solution is {optimal_len} steps")
            else:
                print(f"[A*] solved with {steps} steps, optimal solution is {optimal_len} steps")
    else:
        # No solution found
        if algorithm == "gbfs":
            print(f"[GBFS] no solution, optimal solution is {optimal_len} steps")
        else:
            print(f"[A*] no solution, optimal solution is {optimal_len} steps")

# Problem definitions

#Optimal : 20
Problem_pdf = {
    "Size":   (3, 3),
    "Walls":  {(0, 1), (2, 1)},
    "Taps":   {(1, 1): 6},
    "Plants": {(2, 0): 2, (0, 2): 3},
    "Robots": {10: (1, 0, 0, 2), 11: (1, 2, 0, 2)},
}

# Format reminder:
# {
#   "Size":   (N, M),
#   "Walls":  {(r,c), ...},
#   "Taps":   {(r,c): remaining_water, ...},
#   "Plants": {(r,c): required_water, ...},
#   "Robots": {rid: (r, c, load, capacity), ...}
# }

# -------------------------
# Problem 1: Tiny, no walls
# One robot, one tap, one plant
# -------------------------
#Optimal : 8
problem1 = {
    "Size": (3, 3),
    "Walls": set(),
    "Taps": {(1, 1): 3},
    "Plants": {(0, 2): 2},
    "Robots": {10: (2, 0, 0, 2)},
}

# -------------------------
# Problem 2: Small with walls (your example-style)
# Two robots, one tap, two plants, vertical walls
# -------------------------
#Optimal: 20
problem2 = {
    "Size": (3, 3),
    "Walls": {(0, 1), (2, 1)},
    "Taps": {(1, 1): 6},
    "Plants": {(0, 2): 3, (2, 0): 2},
    "Robots": {10: (1, 0, 0, 2), 11: (1, 2, 0, 2)},
}
# -------------------------
# Problem 3: Corridor with walls, 5x3, one robot shuttling
# -------------------------
#optimal: 28
problem3 = {
    "Size": (5, 3),
    "Walls": {(1, 1), (3, 1)},
    "Taps": {(0, 0): 5},
    "Plants": {(4, 2): 4},
    "Robots": {10: (2, 0, 0, 2)},
}

# -------------------------
# Problem 4
# -------------------------
#optimal: 13
problem4 = {
    "Size": (5, 5),
    "Walls": {(0, 1), (1, 1), (2, 1), (0, 3), (1, 3), (2, 3)},
    "Taps": {(3, 2): 1, (4, 2): 1},
    "Plants": {(0, 2): 1, (1, 2): 1},
    "Robots": {10: (3, 1, 0, 1), 11: (3, 3, 0, 1)},
}

# -------------------------
# Problem 5: Intentional dead-end (not enough water)
# Good to test your dead-end pruning
# -------------------------
problem5_deadend = {
    "Size": (3, 4),
    "Walls": set(),
    "Taps": {(1, 1): 3},
    "Plants": {(0, 3): 2, (2, 3): 2},
    "Robots": {10: (1, 0, 0, 2)},
}
# -------------------------
# Problem 6:
# -------------------------
#optimal: 8
problem6 = {
    "Size": (8, 8),
    "Walls": {
        *( (r, c) for r in range(8) for c in range(8) if not (r == 1 and c in (0, 1, 2)) )
    },
    "Taps": {(1, 1): 3},
    "Plants": {(1, 2): 3},
    "Robots": {10: (1, 0, 0, 3)},
}
#optimal: 21
problem7 = {
    "Size": (4, 4),
    "Walls": set(),
    "Taps": {(2, 2): 18},
    "Plants": {(0, 3): 3, (3, 0): 3},
    "Robots": {10: (2, 1, 0, 3), 11: (2, 0, 0, 3)},
}


def main():
    start = time.time()
    problems = [
        (problem1, 8),
        (problem2, 20),
        (problem3, 28),
        (problem4, 13),
        (problem5_deadend, -1),
        (problem6, 8),
        (problem7, 21),
    ]
    for p, opt in problems:
        for a in ['astar', 'gbfs']:
            solve_problems(p, a, opt)
    end = time.time()
    print('Submission took:', end - start, 'seconds.')

if __name__ == '__main__':
    main()
    # run_and_visualize(problem4)
