from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge

def test_agile_graph():
    ag = AgileGraph()
    n1 = GraphNode(id="1", category="File")
    n2 = GraphNode(id="2", category="CryptoUsage")
    ag.add_node(n1)
    ag.add_node(n2)
    ag.add_edge(GraphEdge(source_id="1", target_id="2", relationship="CONTAINS"))
    
    node = ag.get_node("1")
    assert node is not None
    assert node.category == "File"
    
    neighbors = ag.get_neighbors("1")
    assert "2" in neighbors
