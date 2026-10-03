import pytest
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

def test_no_isolated_duplicate_library_nodes():
    graph = AgileGraph()
    builder = GraphBuilder(graph)
    
    records = [
        FindingRecord(
            asset_type=AssetType.LIBRARY,
            repository="repo",
            file="main.py",
            line=1,
            language=Language.PYTHON,
            library="hashlib",
            evidence="import hashlib",
            confidence=1.0
        )
    ]
    
    builder.build_from_normalized_records(records)
    
    # We should have one file node and one canonical library node
    nodes = list(graph.G.nodes(data=True))
    assert len(nodes) == 2, f"Expected 2 nodes, found {len(nodes)}"
    
    # Check node categories
    categories = [data["category"] for node, data in nodes]
    assert "file" in categories
    assert "library" in categories
    
    # Ensure the library node is the canonical one, not the isolated line-specific finding
    for node, data in nodes:
        if data["category"] == "library":
            assert node == "repo:library:hashlib"
            
    # Check edge
    edges = list(graph.G.edges(data=True))
    assert len(edges) == 1
    source, target, data = edges[0]
    assert source == "repo:main.py"
    assert target == "repo:library:hashlib"
    assert data["relationship"] == "IMPORTS"
