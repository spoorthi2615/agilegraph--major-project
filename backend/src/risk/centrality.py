from src.risk.factors import FactorValue
from src.graph.graph import AgileGraph

def calculate_in_degree_centrality(graph: AgileGraph, node_id: str) -> FactorValue:
    """
    Initial implementation: In-degree centrality normalized by max possible in-degree 
    (number of nodes - 1), or a simple log scale.
    """
    if node_id not in graph.G.nodes:
        return FactorValue(value=None, source="Node not in graph", confidence=0.0)
        
    node_data = graph.G.nodes[node_id]
    if node_data.get("category") != "library":
        return FactorValue(value=None, source="Not applicable for non-library nodes", confidence=0.0)
        
    in_degree = graph.G.in_degree(node_id)
    total_nodes = len(graph.G.nodes)
    
    if total_nodes <= 1:
        return FactorValue(value=0.0, source="in-degree centrality", confidence=1.0)
        
    # Normalization: in_degree / (total_nodes - 1)
    normalized = in_degree / (total_nodes - 1)
    
    return FactorValue(value=normalized, source="in-degree centrality", confidence=1.0)
