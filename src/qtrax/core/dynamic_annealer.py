# src/qtrax/core/dynamic_annealer.py

"""
DynamicAnnealer: Runs a multi-agent, event-driven, quantum-inspired
optimization loop on a changing graph.
"""
import random
import math
from typing import List, Dict, Callable, Any
from src.qtrax.models.problem import Problem
from src.qtrax.models.solution import Solution
from src.qtrax.models.agent import Agent
from src.qtrax.core.neighbor import quantum_jump_neighbor
from src.qtrax.core.annealer import tsp_total_cost

class DynamicAnnealer:
    def __init__(
        self,
        problem: Problem,
        agents: List[Agent],
        event_callback: Callable[[Any], None] = None, # type: ignore
        max_tick: int = 100,
        mini_iter: int = 200,
        start_temp: float = 100.0,
        cooling_rate: float = 0.9,
        min_temp: float = 1e-2,
        quantum_jump_prob: float = 0.05,
        random_seed: int = 42
    ):
        """
        :param problem: Dynamic Problem (graph) instance
        :param agents: List of Agent objects to route simultaneously
        :param event_callback: If provided, called each tick to inject dynamic events
        :param max_tick: Maximum time steps to simulate
        :param mini_iter: Number of SA iterations per agent per tick (local search depth)
        :param start_temp, cooling_rate, min_temp: SA hyperparameters (per-tick local)
        :param quantum_jump_prob: Probability of a quantum jump neighbor
        """
        self.problem = problem
        self.agents = agents
        self.event_callback = event_callback
        self.max_tick = max_tick
        self.mini_iter = mini_iter
        self.start_temp = start_temp
        self.cooling_rate = cooling_rate
        self.min_temp = min_temp
        self.quantum_jump_prob = quantum_jump_prob
        self.random_seed = random_seed
        random.seed(random_seed)

        # Keep track of each agent’s latest mini-solution
        self.agent_solutions: Dict[str, Solution] = {agent.id: None for agent in agents} # type: ignore

    def _acceptance_probability(self, old_cost: float, new_cost: float, temperature: float) -> float:
        if new_cost < old_cost:
            return 1.0
        return math.exp((old_cost - new_cost) / (temperature + 1e-9))

    def _local_sa(self, agent: Agent) -> Solution:
        """
        Run a small SA pass from the agent’s current node to its goal,
        but only to decide the immediate next node.
        We build a “mini-route”: current_node -> ... -> goal_node -> current_node
        so that it forms a cycle, run SA, then return the first step.
        """
        # Build a “subproblem” containing only nodes still active, or entire graph if simpler.
        # For simplicity, we’ll let the entire problem be used, but start at current_node.
        # Initial route: randomly shuffle all nodes, then ensure start/end at current_node.
        nodes = [n.id for n in self.problem.nodes]
        route = nodes.copy()
        random.shuffle(route)
        if route[0] != agent.current_node:
            try:
                idx = route.index(agent.current_node)
                route[0], route[idx] = route[idx], route[0]
            except ValueError:
                route.insert(0, agent.current_node)
        if route[-1] != agent.current_node:
            route.append(agent.current_node)

        # Wrap into a Solution (cost will be calculated)
        current_solution = Solution(route, None) # type: ignore

        best = current_solution
        best_cost = tsp_total_cost(best, self.problem)
        temperature = self.start_temp

        # Mini-SA loop
        for _ in range(self.mini_iter):
            neighbor = quantum_jump_neighbor(best, self.problem, jump_prob=self.quantum_jump_prob)
            cost_neighbor = tsp_total_cost(neighbor, self.problem)
            ap = self._acceptance_probability(best_cost, cost_neighbor, temperature)
            if random.random() < ap:
                best = neighbor
                best_cost = cost_neighbor
            temperature *= self.cooling_rate
            if temperature < self.min_temp:
                break

        return best

    def _detect_collisions(self, proposed_moves: Dict[str, int]) -> List[str]:
        """
        Given a dict of agent_id -> next_node, return list of agent_ids that collide.
        If two or more agents propose the same next_node, then none of them move.
        """
        reverse_map: Dict[int, List[str]] = {}
        for aid, node in proposed_moves.items():
            reverse_map.setdefault(node, []).append(aid)

        collisions = []
        for node, aids in reverse_map.items():
            if len(aids) > 1:
                collisions.extend(aids) # type: ignore
        return collisions # type: ignore

    def run(self) -> None:
        """
        Executes the dynamic, multi-agent simulation loop:
        - For each tick:
          1. Fire any event callback (to update graph).
          2. For each active agent: run mini-SA to find best route, pick immediate next node.
          3. Detect collisions. Agents in collision do not move or are re-routed.
          4. Update agent positions, statuses.
        - Ends when all agents are completed or max_tick is reached.
        """
        tick = 0
        while tick < self.max_tick:
            # 1) Dynamic events can change the graph
            if self.event_callback: # type: ignore
                self.event_callback(tick)

            # 2) For each active agent, run a mini-SA to pick next node
            proposed_moves: Dict[str, int] = {}
            for agent in self.agents:
                if agent.status != 'active':
                    continue

                # If agent is already at goal, skip
                if agent.current_node == agent.goal_node:
                    agent.status = 'completed'
                    continue

                # Run local SA to get a good route candidate (cycle)
                best_solution = self._local_sa(agent)
                # The first two entries in best_solution.routes are [current_node, next_node, ...]
                current_idx = best_solution.routes.index(agent.current_node)
                next_idx = (current_idx + 1) % len(best_solution.routes)
                next_node = best_solution.routes[next_idx]
                proposed_moves[agent.id] = next_node
                # Save the full solution for possible debugging/analysis
                self.agent_solutions[agent.id] = best_solution

            # 3) Detect collisions
            collisions = self._detect_collisions(proposed_moves)
            for aid in collisions:
                # Block those agents from moving this tick
                del proposed_moves[aid]
                # Mark them as “blocked” or skip; we can optionally re-schedule next tick
                agent = next(a for a in self.agents if a.id == aid)
                agent.status = 'blocked'

            # 4) Commit moves for non-colliding agents
            for agent_id, next_node in proposed_moves.items():
                agent = next(a for a in self.agents if a.id == agent_id)
                agent.step_to(next_node)

            # 5) Unblock any previously blocked agents (so they can try again next tick)
            for agent in self.agents:
                if agent.status == 'blocked':
                    agent.status = 'active'

            # Check if all are done
            if all(agent.status == 'completed' for agent in self.agents):
                print(f"All agents completed by tick {tick}.")
                break

            tick += 1

        # Simulation ended. Agents have their route histories in agent.route
        print(f"Simulation ended at tick {tick}.")
