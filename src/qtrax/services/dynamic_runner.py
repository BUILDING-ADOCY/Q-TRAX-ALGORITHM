# src/qtrax/services/dynamic_runner.py

"""
Service to orchestrate dynamic, multi-agent solves using DynamicAnnealer.
"""
from typing import List, Dict, Any
from src.qtrax.models.agent import Agent
from src.qtrax.models.problem import Problem  # type: ignore # used for type hints if desired
from src.qtrax.models.solution import Solution
from src.qtrax.core.dynamic_annealer import DynamicAnnealer
from src.qtrax.utils.io_helpers import load_problem_yaml, load_problem_json, save_solution_json
from src.qtrax.utils.event_bus import EventBus


def load_agents_from_config(config: Dict[str, Any]) -> List[Agent]:
    """
    Parse the 'agents' list from the config dictionary and return a list of Agent objects.
    Expected format in config:
        agents:
          - id: "A1"
            start: 1
            goal: 5
          - id: "A2"
            start: 2
            goal: 4
    """
    agents_data = config.get("agents", [])
    agents: List[Agent] = []
    for entry in agents_data:
        aid = entry["id"]
        start = entry["start"]
        goal = entry["goal"]
        agents.append(Agent(agent_id=aid, start_node=start, goal_node=goal))
    return agents


def dynamic_solve(
    config_path: str,
    output_path: str,
    use_yaml: bool = True,
    max_tick: int = 50
) -> Dict[str, Any]:
    """
    1. Load Problem (graph) from YAML/JSON.
    2. Load Agents from the same config file (expects 'agents' key).
    3. Register any event callbacks (e.g., block an edge at a certain tick).
    4. Instantiate DynamicAnnealer and run simulation.
    5. Collect each agent's route/status, save to JSON, and return results.

    :param config_path: Path to a YAML/JSON file containing 'nodes', 'edges', 'constraints', and 'agents'.
    :param output_path: Path where to write a JSON file summarizing all agents' routes/status.
    :param use_yaml: If True, treat config_path as YAML; if False, as JSON.
    :param max_tick: Maximum number of ticks/steps to simulate.
    :return: A dict mapping agent_id -> {"route": [...], "status": "..."}.
    """
    # 1) Load the Problem (graph)
    if use_yaml:
        problem = load_problem_yaml(config_path)
    else:
        problem = load_problem_json(config_path)

    # 2) Parse agents from the same config
    import yaml, json  # type: ignore
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f) if use_yaml else json.load(f)
    agents = load_agents_from_config(raw)

    # 3) Example event callback: block edge (2->3) at tick=10
    def on_tick(tick: int):
        if tick == 10:
            print("Event: Blocking edge 2->3 at tick 10")
            problem.remove_edge(2, 3)
            EventBus.publish("edge_blocked", {"source": 2, "target": 3})

    # Subscribe to the same event just to log it
    EventBus.subscribe("edge_blocked", lambda data: print(f"EventBus: Edge removed {data}"))

    # 4) Instantiate DynamicAnnealer
    dynamic_annealer = DynamicAnnealer(
        problem=problem,
        agents=agents,
        event_callback=on_tick,
        max_tick=max_tick,
        mini_iter=200,
        start_temp=100.0,
        cooling_rate=0.9,
        min_temp=1e-2,
        quantum_jump_prob=0.1,
        random_seed=42
    )

    # 5) Run the simulation loop
    dynamic_annealer.run()

    # 6) Collect results: each agent's route and status
    results: Dict[str, Any] = {}
    for agent in agents:
        results[agent.id] = {
            "route": agent.route,
            "status": agent.status
        }

    # 7) Save results to JSON:
    # We wrap results in a Solution so that save_solution_json serializes it consistently.
    save_solution_json(Solution(routes=results, total_cost=0, meta={}), output_path)
    print(f"Dynamic solution written to {output_path}")

    return results
