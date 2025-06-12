"""
Command-line entrypoint for QU-TRAX: load a problem, solve it (static or dynamic),
and write out solution.
"""
import argparse
import os

from src.qtrax.utils.io_helpers import load_problem_yaml, load_problem_json, save_solution_json
from src.qtrax.services.runner import solve as static_solve
from src.qtrax.services.dynamic_runner import dynamic_solve


def main():
    parser = argparse.ArgumentParser(
        description="Q-TRAX: Quantum-Inspired Logistics Optimizer"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Path to problem definition (YAML or JSON). "
             "For static mode, file needs only `nodes`/`edges`/`constraints`. "
             "For dynamic mode, file also needs an `agents:` list."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="solution.json",
        help="Path to write the solution JSON."
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["static", "dynamic"],
        default="static",
        help="Choose `static` for single-agent SA or `dynamic` for multi-agent, event-driven SA."
    )
    parser.add_argument(
        "--max-tick", "-t",
        type=int,
        default=50,
        help="(Dynamic only) Maximum number of ticks/steps to simulate."
    )

    args = parser.parse_args()
    config_path = args.config

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    ext = os.path.splitext(config_path)[1].lower()
    if ext not in [".yaml", ".yml", ".json"]:
        raise ValueError("Unsupported config format. Use .yaml, .yml, or .json")

    # --- STATIC MODE ---
    if args.mode == "static":
        if ext in [".yaml", ".yml"]:
            problem = load_problem_yaml(config_path)
        else:
            problem = load_problem_json(config_path)

        solution = static_solve(problem)
        save_solution_json(solution, args.output)
        print(f"Static solution written to: {args.output}")
        print(f"Total cost: {solution.total_cost:.2f}")
        return

    # --- DYNAMIC MODE ---
    # In dynamic mode, we expect the same config file to include an `agents:` section.
    # dynamic_solve will load both graph and agents from that file.
    results = dynamic_solve(
        config_path=config_path,
        output_path=args.output,
        use_yaml=(ext in [".yaml", ".yml"]),
        max_tick=args.max_tick
    )

    print(f"Dynamic solution written to: {args.output}")
    print("Agent results:")
    for agent_id, info in results.items():
        route_str = ", ".join(str(n) for n in info["route"])
        print(f"  • Agent {agent_id}: status={info['status']}, route=[{route_str}]")


if __name__ == "__main__":
    main()
