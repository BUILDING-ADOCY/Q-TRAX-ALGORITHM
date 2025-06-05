import random
from src.qtrax.models.solution import Solution
from src.qtrax.models.problem import Problem

def tsp_2opt_neighbor(current_solution: Solution, problem: Problem) -> Solution:
    # Neighbor function logic as discussed before
    route = current_solution.routes.copy()
    if len(route) < 4:
        return Solution(route, current_solution.total_cost, current_solution.meta)
    i, j = sorted(random.sample(range(1, len(route)-1), 2))
    route[i:j] = reversed(route[i:j])
    return Solution(route, None, current_solution.meta) # type: ignore