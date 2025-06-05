# src/qtrax/models/agent.py

"""
Represents a single agent (e.g., delivery bot or drone) in a dynamic environment.
Tracks position, goal, and route history.
"""
from typing import List, Any # type: ignore

class Agent:
    def __init__(self, agent_id: str, start_node: int, goal_node: int):
        """
        :param agent_id: Unique identifier for this agent (e.g., "A1", "drone_02").
        :param start_node: The node ID where this agent begins.
        :param goal_node: The node ID where this agent must end.
        """
        self.id = agent_id
        self.current_node = start_node      # where the agent is currently located
        self.goal_node = goal_node          # destination node
        self.route: List[int] = [start_node]  # history of nodes visited
        self.status: str = 'active'         # 'active', 'completed', or 'blocked'

    def step_to(self, next_node: int) -> None:
        """
        Move the agent from its current_node to next_node. Append next_node to the route.
        If next_node equals the goal_node, set status to 'completed'.
        """
        self.current_node = next_node
        self.route.append(next_node)
        if self.current_node == self.goal_node:
            self.status = 'completed'

    def reset(self, new_start: int, new_goal: int) -> None:
        """
        Reinitialize the agent with a new start and new goal (e.g., for reruns or new scenarios).
        """
        self.current_node = new_start
        self.goal_node = new_goal
        self.route = [new_start]
        self.status = 'active'

    def __repr__(self) -> str:
        return (
            f"Agent(id={self.id}, "
            f"current={self.current_node}, "
            f"goal={self.goal_node}, "
            f"status={self.status})"
        )
