"""
Command-line entrypoint for Q-TRAX: load a problem, solve it, and write out solution.
"""
import argparse
import os
from src.qtrax.utils.io_helpers import load_problem_yaml, save_solution_json
from src.qtrax.services.runner import solve

print("Problem class test:")
from src.qtrax.models.problem import Problem
print(Problem)

# exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Q-TRAX: Quantum-Inspired Logistics Optimizer"
    )
    parser.add_argument(
        "--config", "-c", type=str, required=True,
        help="Path to problem definition (YAML or JSON)."
    )
    parser.add_argument(
        "--output", "-o", type=str, default="solution.json",
        help="Path to write the solution JSON."
    )
    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Determine file extension and load accordingly
    ext = os.path.splitext(config_path)[1].lower()
    if ext in [".yaml", ".yml"]:
        problem = load_problem_yaml(config_path)
    elif ext == ".json":
        from src.qtrax.utils.io_helpers import load_problem_json
        problem = load_problem_json(config_path)
    else:
        raise ValueError("Unsupported config format. Use .yaml, .yml, or .json")

    # Solve the problem
    solution = solve(problem)

    # Save the solution
    save_solution_json(solution, args.output)
    print(f"Solution written to: {args.output}")
    print(f"Total cost: {solution.total_cost:.2f}")


if __name__ == "__main__":
    main()
