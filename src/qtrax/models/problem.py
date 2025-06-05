"""

Problem definition for Q-TRAX Algorithm.
Models nodes, edges, and constraints for logistics optimization.

"""
from typing import Dict, Any, List, Optional
import networkx as nx # type: ignore

class Node:
    """
    Represents a location (depot, warehouse, delivery point, etc.).
    """
    def __init__(self, node_id: int, attributes: Optional[Dict[str, Any]] = None):
        self.id = node_id
        self.attributes = attributes or {}

    def __repr__(self):
        return f"Node(id={self.id}, attributes={self.attributes})"

class Edge:
    """
    Represents a weighted edge between two nodes (distance, cost, time, etc.).
    """
    def __init__(self, source: int, target: int, weight: float, attributes: Optional[Dict[str, Any]] = None):
        self.source = source
        self.target = target
        self.weight = weight
        self.attributes = attributes or {}

    def __repr__(self):
        return f"Edge({self.source} -> {self.target}, weight={self.weight}, attributes={self.attributes})"

class Problem:
    pass
    """
    Full logistics problem definition: graph + constraints.
    Uses NetworkX graph for performance and advanced features.
    """
    def __init__(
        self,
        nodes: List[Node],
        edges: List[Edge],
        constraints: Optional[Dict[str, Any]] = None,
    ):
        self.nodes = nodes
        self.edges = edges
        self.constraints = constraints or {}
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node.id, **node.attributes)  # type: ignore
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, weight=edge.weight, **edge.attributes)  # type: ignore
        return G

    def get_neighbors(self, node_id: int) -> List[int]:
        return list(self.graph.successors(node_id))  # type: ignore

    def distance(self, source: int, target: int) -> float:
        if not self.graph.has_edge(source, target): # type: ignore
            raise ValueError(f"No edge from {source} to {target}")
        return self.graph.edges[source, target]['weight']  # type: ignore

    def __repr__(self):
        return f"Problem(nodes={len(self.nodes)}, edges={len(self.edges)}, constraints={self.constraints})"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Problem':
        nodes = [Node(n['id'], n.get('attributes')) for n in data['nodes']]
        edges = [Edge(e['source'], e['target'], e['weight'], e.get('attributes')) for e in data['edges']]
        constraints = data.get('constraints', {})
        return Problem(nodes, edges, constraints)
