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
