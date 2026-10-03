from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

def test_builder_crypto_usage():
    ag = AgileGraph()
    builder = GraphBuilder(ag)
    
    records = [
        FindingRecord(
            asset_type=AssetType.CRYPTO_USAGE,
            repository="repo",
            file="main.py",
            line=10,
            language=Language.PYTHON,
            library="hashlib",
            api="hashlib.md5",
            evidence="hashlib.md5()",
            confidence=1.0
        )
    ]
    builder.build_from_normalized_records(records)
    
    file_node = ag.get_node("repo:main.py")
    assert file_node is not None
    assert file_node.category == "file"
    
    usage_node_id = "repo:main.py:10:hashlib.md5"
    usage_node = ag.get_node(usage_node_id)
    assert usage_node is not None
    assert usage_node.category == "crypto_usage"
    
    lib_node = ag.get_node("repo:library:hashlib")
    assert lib_node is not None
    
    # Check edges
    neighbors_file = ag.get_neighbors("repo:main.py")
    assert usage_node_id in neighbors_file
    
    neighbors_usage = ag.get_neighbors(usage_node_id)
    assert "repo:library:hashlib" in neighbors_usage

def test_builder_imports():
    ag = AgileGraph()
    builder = GraphBuilder(ag)
    
    records = [
        FindingRecord(
            asset_type=AssetType.LIBRARY,
            repository="repo",
            file="main.go",
            line=2,
            language=Language.GO,
            library="crypto/aes",
            evidence="import crypto/aes",
            confidence=1.0
        )
    ]
    builder.build_from_normalized_records(records)
    
    neighbors_file = ag.get_neighbors("repo:main.go")
    assert "repo:library:crypto/aes" in neighbors_file
