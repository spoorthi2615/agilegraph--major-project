from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.graph.validation import validate_graph

def test_validate_valid_graph():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="f1", category="file", properties={"file": "a.py"}))
    ag.add_node(GraphNode(id="c1", category="crypto_usage"))
    ag.add_edge(GraphEdge(source_id="f1", target_id="c1", relationship="CONTAINS"))
    
    errors = validate_graph(ag)
    assert len(errors) == 0

def test_validate_invalid_node_category():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="n1", category="invalid_cat"))
    
    errors = validate_graph(ag)
    assert len(errors) == 1
    assert "invalid category" in errors[0]

def test_validate_invalid_edge_relationship():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="f1", category="file", properties={"file": "a.py"}))
    ag.add_node(GraphNode(id="c1", category="crypto_usage"))
    ag.add_edge(GraphEdge(source_id="f1", target_id="c1", relationship="BOGUS_EDGE"))
    
    errors = validate_graph(ag)
    assert len(errors) == 1
    assert "invalid relationship" in errors[0]
    
def test_validate_missing_file_property():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="f1", category="file")) # missing file property
    errors = validate_graph(ag)
    assert len(errors) == 1
    assert "missing 'file' property" in errors[0]
