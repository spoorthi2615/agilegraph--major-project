import networkx as nx
from typing import List, Optional, Dict
from src.graph.schema import GraphNode, GraphEdge
from src.graph.validation import validate_graph

class AgileGraph:
    def __init__(self):
        self.G = nx.MultiDiGraph()

    def add_node(self, node: GraphNode):
        self.G.add_node(node.id, category=node.category, **node.properties)

    def add_edge(self, edge: GraphEdge):
        self.G.add_edge(edge.source_id, edge.target_id, key=edge.relationship, relationship=edge.relationship, **edge.properties)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        if node_id in self.G:
            data = self.G.nodes[node_id]
            category = data.get("category", "Unknown")
            properties = {k: v for k, v in data.items() if k != "category"}
            return GraphNode(id=node_id, category=category, properties=properties)
        return None

    def get_neighbors(self, node_id: str) -> List[str]:
        if node_id in self.G:
            return list(self.G.successors(node_id)) + list(self.G.predecessors(node_id))
        return []

    def validate_integrity(self) -> List[str]:
        """
        Validates no dangling edges, non-empty graph, and schema-legal edge triplets
        per Synopsis 5.3. Returns list of error strings (empty if valid).
        """
        return validate_graph(self)
