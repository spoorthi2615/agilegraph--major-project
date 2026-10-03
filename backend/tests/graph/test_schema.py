from src.graph.schema import GraphNode, GraphEdge

def test_graph_node():
    n = GraphNode(id="n1", category="File", properties={"file": "a.py"})
    assert n.id == "n1"
    assert n.category == "File"
    assert n.properties["file"] == "a.py"

def test_graph_edge():
    e = GraphEdge(source_id="n1", target_id="n2", relationship="CONTAINS")
    assert e.source_id == "n1"
    assert e.relationship == "CONTAINS"
