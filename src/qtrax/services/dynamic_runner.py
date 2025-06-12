# src/qtrax/services/dynamic_runner.py

"""
Service to orchestrate dynamic, multi-agent solves using DynamicAnnealer.
"""
from typing import List, Dict, Any
import yaml, json  # type: ignore
from src.qtrax.models.agent import Agent
from src.qtrax.models.problem import Problem  # type: ignore
from src.qtrax.models.solution import Solution
from src.qtrax.core.dynamic_annealer import DynamicAnnealer
from src.qtrax.utils.io_helpers import load_problem_yaml, load_problem_json, save_solution_json
from src.qtrax.utils.event_bus import EventBus


def load_agents_from_config(config: Dict[str, Any]) -> List[Agent]:
    agents_data = config.get("agents", [])
    agents: List[Agent] = []
    for entry in agents_data:
        agents.append(Agent(
            agent_id=entry["id"],
            start_node=entry["start"],
            goal_node=entry["goal"]
        ))
    return agents


def dynamic_solve(
    config_path: str,
    output_path: str,
    use_yaml: bool = True,
    max_tick: int = 50
) -> Dict[str, Any]:
    # 1) Load the Problem
    problem = load_problem_yaml(config_path) if use_yaml else load_problem_json(config_path)

    # 2) Load raw config for agents
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f) if use_yaml else json.load(f)
    agents = load_agents_from_config(raw)

    # 3) Register an example event callback
    def on_tick(tick: int):
        if tick == 10:
            print("Event: Blocking edge 2->3 at tick 10")
            try:
                problem.remove_edge(2, 3)
                EventBus.publish("edge_blocked", {"source": 2, "target": 3})
            except Exception as e:
                import logging
                logging.exception(f"Error in on_tick at tick={tick}: {e}")

    EventBus.subscribe("edge_blocked", lambda data: print(f"EventBus: Edge removed {data}"))

    # 4) Instantiate and run the annealer
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
    dynamic_annealer.run()

    # 5) Collect each agent's route/status
    results: Dict[str, Any] = {
        agent.id: {"route": agent.route, "status": agent.status}
        for agent in agents
    }

    # 6) Save results
    save_solution_json(Solution(routes=results, total_cost=0, meta={}), output_path)
    print(f"Dynamic solution written to {output_path}")

    return results
