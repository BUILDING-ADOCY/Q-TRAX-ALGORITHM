"""
Orchestrates problem loading, annealing, and final solution output.
"""
from typing import Any, Dict  # type: ignore
from src.qtrax.models.problem import Problem
from src.qtrax.models.solution import Solution
from src.qtrax.core.annealer import (
    Annealer,
    tsp_total_cost,
    tsp_initial_solution,
)
from src.qtrax.core.neighbor import tsp_2opt_neighbor
from src.qtrax.config import settings

def solve(problem: Problem) -> Solution:
    """
    Run the annealer on the given Problem and return the best Solution.
    """
    print("solve called")  # For debugging; remove or comment for production

    annealer = Annealer(
        problem=problem,
        initial_solution_fn=tsp_initial_solution,
        neighbor_fn=tsp_2opt_neighbor,
        cost_fn=tsp_total_cost,
        max_iter=getattr(settings, "max_iterations", 10000),
        start_temp=getattr(settings, "start_temp", 1000.0),
        cooling_rate=getattr(settings, "cooling_rate", 0.995),
        min_temp=getattr(settings, "min_temp", 1e-3),
        random_seed=getattr(settings, "random_seed", 42),
    )

    best_solution = annealer.run()
    # Recompute and assign final total_cost (in case cost was None)
    best_solution.total_cost = tsp_total_cost(best_solution, problem)
    return best_solution
