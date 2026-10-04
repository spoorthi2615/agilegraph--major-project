from src.risk.factor_extractor import FactorExtractor
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode

def test_factor_extractor_complete_fixture():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="lib1", category="library"))
    # Add a dummy edge to give it an in-degree of 1
    ag.G.add_node("file1")
    ag.G.add_edge("file1", "lib1")
    
    metadata = {
        "data_classification": "HIGH",
        "business_criticality": "CRITICAL",
        "network_exposure": "INTERNET_FACING"
    }
    cve_info = {"status": "success", "cves": ["CVE-2023-1234"]}
    migration_inputs = {"code_change": 10, "dependency_change": 5}
    algorithm = "rsa"
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("lib1", metadata, cve_info, migration_inputs, algorithm)
    
    assert factors.data_sensitivity.value == 0.75
    assert factors.asset_criticality.value == 1.0
    assert factors.internet_exposure.value == 1.0
    assert factors.crypto_weakness.value == 0.9
    assert factors.cve_risk.value == 1.0
    assert factors.library_centrality.value == 1.0 # 1 / (2-1)
    assert factors.migration_difficulty.value == 0.7 # (1.0*0.4) + (1.0*0.3)

def test_factor_extractor_incomplete_fixture():
    ag = AgileGraph()
    extractor = FactorExtractor(ag)
    
    factors = extractor.extract("lib1", {}, {"status": "unavailable"}, {}, None)
    
    assert factors.data_sensitivity.value is None
    assert factors.asset_criticality.value is None
    assert factors.internet_exposure.value is None
    assert factors.crypto_weakness.value is None
    assert factors.cve_risk.value is None
    assert factors.migration_difficulty.value is None

def test_factor_extractor_graph_traversal_weak_algo():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="usage_md5", category="crypto_usage", properties={"algorithm": "md5"}))
    ag.add_node(GraphNode(id="usage_aes", category="crypto_usage", properties={"algorithm": "aes"}))
    
    from src.graph.schema import GraphEdge
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_md5", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_aes", relationship="CONTAINS"))
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("file1", {}, {}, {})
    
    # MD5 should be prioritized as the weakest algorithm
    assert factors.crypto_weakness.value > 0.5
    assert "md5" in factors.crypto_weakness.source.lower()

def test_factor_extractor_graph_traversal_strong_algo():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="usage_aes", category="crypto_usage", properties={"algorithm": "aes"}))
    
    from src.graph.schema import GraphEdge
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_aes", relationship="CONTAINS"))
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("file1", {}, {}, {})
    
    # AES should not be 1.0 risk (it's safe, but let's check what algorithm_strength.py returns)
    assert factors.crypto_weakness.value == 0.3 # AES is currently safe in the system
    assert "aes" in factors.crypto_weakness.source.lower()

def test_factor_extractor_graph_traversal_rsa_keysize():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="usage_rsa_1024", category="crypto_usage", properties={"algorithm": "rsa", "key_size": 1024}))
    ag.add_node(GraphNode(id="file2", category="file"))
    ag.add_node(GraphNode(id="usage_rsa_4096", category="crypto_usage", properties={"algorithm": "rsa", "key_size": 4096}))
    
    from src.graph.schema import GraphEdge
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_rsa_1024", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file2", target_id="usage_rsa_4096", relationship="CONTAINS"))
    
    extractor = FactorExtractor(ag)
    factors1 = extractor.extract("file1", {}, {}, {})
    factors2 = extractor.extract("file2", {}, {}, {})
    
    assert factors1.crypto_weakness.value == 1.0
    assert factors2.crypto_weakness.value == 0.8
    assert factors1.crypto_weakness.value != factors2.crypto_weakness.value

def test_factor_extractor_graph_traversal_aes_and_rsa():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="usage_aes", category="crypto_usage", properties={"algorithm": "aes"}))
    ag.add_node(GraphNode(id="usage_rsa_1024", category="crypto_usage", properties={"algorithm": "rsa", "key_size": 1024}))
    
    from src.graph.schema import GraphEdge
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_aes", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_rsa_1024", relationship="CONTAINS"))
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("file1", {}, {}, {})
    
    # AES (0.3) < RSA-1024 (1.0), so 1.0 should be chosen
    assert factors.crypto_weakness.value == 1.0
    assert "rsa" in factors.crypto_weakness.source.lower()

def test_factor_extractor_graph_traversal_aes_and_none():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="usage_aes", category="crypto_usage", properties={"algorithm": "aes"}))
    ag.add_node(GraphNode(id="usage_none", category="crypto_usage", properties={"algorithm": "none"}))
    
    from src.graph.schema import GraphEdge
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_aes", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file1", target_id="usage_none", relationship="CONTAINS"))
    
    extractor = FactorExtractor(ag)
    factors = extractor.extract("file1", {}, {}, {})
    
    # none (1.0) > AES (0.3), so 1.0 should be chosen, ensuring none isn't masked
    assert factors.crypto_weakness.value == 1.0
    assert "none" in factors.crypto_weakness.source.lower()

