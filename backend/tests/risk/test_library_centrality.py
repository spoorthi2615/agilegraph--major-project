import pytest
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.risk.centrality import calculate_in_degree_centrality, calculate_library_centrality_for_file
from src.risk.factor_extractor import FactorExtractor


def test_file_library_centrality_aggregation():
    """
    Verifies that a file importing libraries receives the peak in-degree centrality
    among its connected libraries.
    """
    ag = AgileGraph()
    # Create 3 files and 2 libraries
    ag.add_node(GraphNode(id="proj:f1.py", category="file", properties={"file": "f1.py"}))
    ag.add_node(GraphNode(id="proj:f2.py", category="file", properties={"file": "f2.py"}))
    ag.add_node(GraphNode(id="proj:f3.py", category="file", properties={"file": "f3.py"}))
    
    ag.add_node(GraphNode(id="proj:lib:popular", category="library", properties={"library": "popular"}))
    ag.add_node(GraphNode(id="proj:lib:niche", category="library", properties={"library": "niche"}))
    
    # popular is imported by f1, f2, f3 -> in_degree = 3
    ag.add_edge(GraphEdge(source_id="proj:f1.py", target_id="proj:lib:popular", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="proj:f2.py", target_id="proj:lib:popular", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="proj:f3.py", target_id="proj:lib:popular", relationship="IMPORTS"))
    
    # niche is imported only by f1 -> in_degree = 1
    ag.add_edge(GraphEdge(source_id="proj:f1.py", target_id="proj:lib:niche", relationship="IMPORTS"))
    
    # Total nodes = 5. Max possible in-degree = 5 - 1 = 4.
    # Centrality of popular = 3 / 4 = 0.75
    # Centrality of niche = 1 / 4 = 0.25
    
    res = calculate_library_centrality_for_file(ag, "proj:f1.py")
    assert res.value == 0.75
    assert "popular" in res.source
    assert res.confidence == 0.85


def test_file_with_no_connected_libraries_returns_none():
    """
    Verifies that a file with no imported libraries returns value=None (missing data),
    preventing silent conversion to a misleading 0.0.
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="proj:f1.py", category="file", properties={"file": "f1.py"}))
    ag.add_node(GraphNode(id="proj:lib:some_lib", category="library", properties={"library": "some_lib"}))
    
    res = calculate_library_centrality_for_file(ag, "proj:f1.py")
    assert res.value is None
    assert res.source == "no connected libraries"
    assert res.confidence == 0.0


def test_graph_with_no_libraries_returns_none():
    """
    Verifies that a graph containing no library nodes returns value=None.
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="proj:f1.py", category="file", properties={"file": "f1.py"}))
    
    res = calculate_library_centrality_for_file(ag, "proj:f1.py")
    assert res.value is None
    assert res.source == "no connected libraries"


def test_direct_library_centrality_preserved():
    """
    Verifies that calling calculate_in_degree_centrality directly on a library node
    continues to return the library's normalized in-degree.
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="proj:f1.py", category="file", properties={"file": "f1.py"}))
    ag.add_node(GraphNode(id="proj:lib:core", category="library", properties={"library": "core"}))
    ag.add_edge(GraphEdge(source_id="proj:f1.py", target_id="proj:lib:core", relationship="IMPORTS"))
    
    # 2 nodes, in-degree = 1. Centrality = 1 / (2 - 1) = 1.0
    res = calculate_in_degree_centrality(ag, "proj:lib:core")
    assert res.value == 1.0
    assert res.confidence == 1.0


def test_factor_extractor_populates_library_centrality():
    """
    Verifies that FactorExtractor automatically populates library_centrality on file assets.
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="proj:f1.py", category="file", properties={"file": "f1.py"}))
    ag.add_node(GraphNode(id="proj:f2.py", category="file", properties={"file": "f2.py"}))
    ag.add_node(GraphNode(id="proj:lib:shared", category="library", properties={"library": "shared"}))
    
    ag.add_edge(GraphEdge(source_id="proj:f1.py", target_id="proj:lib:shared", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="proj:f2.py", target_id="proj:lib:shared", relationship="IMPORTS"))
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("proj:f1.py", {}, {}, {})
    # Total nodes = 3. In-degree of shared = 2. Centrality = 2 / 2 = 1.0
    assert factors.library_centrality.value == 1.0
    assert "shared" in factors.library_centrality.source
