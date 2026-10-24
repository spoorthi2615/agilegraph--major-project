from src.risk.factor_extractor import FactorExtractor
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge

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

def test_factor_extractor_all_seven_factors_positive_and_negative():
    """Explicitly verifies positive extraction, negative/missing states, and that unknown != 0.0 for all 7 factors."""
    from src.graph.schema import GraphEdge
    # Positive case: graph contains evidence for sensitivity, exposure, crypto, cve, centrality, migration
    ag_pos = AgileGraph()
    ag_pos.add_node(GraphNode(id="file1", category="file", properties={"file": "src/auth/login.py"}))
    ag_pos.add_node(GraphNode(id="ep1", category="endpoint", properties={"network_exposure": "INTERNET_FACING", "path": "/login"}))
    ag_pos.add_node(GraphNode(id="sd1", category="sensitive_data", properties={"classification": "HIGH", "name": "user_token"}))
    ag_pos.add_node(GraphNode(id="cu1", category="crypto_usage", properties={"algorithm": "rsa", "key_size": 2048}))
    ag_pos.add_node(GraphNode(id="lib1", category="library", properties={"library": "requests", "version": "2.28.0"}))
    ag_pos.add_node(GraphNode(id="file2", category="file", properties={"file": "src/other.py"}))

    ag_pos.add_edge(GraphEdge(source_id="file1", target_id="ep1", relationship="EXPOSES"))
    ag_pos.add_edge(GraphEdge(source_id="file1", target_id="sd1", relationship="PROTECTS"))
    ag_pos.add_edge(GraphEdge(source_id="file1", target_id="cu1", relationship="CONTAINS"))
    ag_pos.add_edge(GraphEdge(source_id="file1", target_id="lib1", relationship="IMPORTS"))
    ag_pos.add_edge(GraphEdge(source_id="file2", target_id="lib1", relationship="IMPORTS"))

    extractor_pos = FactorExtractor(ag_pos)
    factors_pos = extractor_pos.extract("file1", {"file": "src/auth/login.py"}, {"status": "success", "cves": ["CVE-2023-1234"]}, {})

    # Positive assertions
    assert factors_pos.crypto_weakness.value == 0.9, "RSA 2048 should be 0.9"
    assert factors_pos.data_sensitivity.value == 0.75, "HIGH classification should be 0.75"
    assert factors_pos.asset_criticality.value == 0.75, "auth/ path should infer 0.75 criticality"
    assert factors_pos.internet_exposure.value == 1.0, "INTERNET_FACING endpoint should be 1.0"
    assert factors_pos.cve_risk.value == 1.0, "CVE present should be 1.0"
    assert factors_pos.migration_difficulty.value is not None, "Migration difficulty should be computed"
    assert factors_pos.migration_difficulty.value > 0.0

    # Negative case: bare file with no connected assets and unavailable external services
    ag_neg = AgileGraph()
    ag_neg.add_node(GraphNode(id="bare_file.py", category="file", properties={"file": "bare_file.py"}))
    extractor_neg = FactorExtractor(ag_neg)
    factors_neg = extractor_neg.extract("bare_file.py", {"file": "bare_file.py"}, {"status": "unavailable"}, {})

    # Verify each unknown factor is None, and strictly NOT 0.0
    for factor_name, fv in factors_neg.model_dump().items():
        if factor_name != "library_centrality": # bare file node is not library
            assert fv["value"] is None, f"{factor_name} must be None when no evidence exists, got {fv['value']}"
            assert fv["value"] != 0.0, f"{factor_name} must NOT be converted to 0.0 (would imply zero risk)"


def test_endpoint_exposure_propagation_deterministic_pipeline(tmp_path):
    """
    Traces explicit INTERNET_FACING exposure from scanner finding -> graph node -> edge -> factors -> final score.
    """
    from src.pipeline.runner import run_pipeline
    repo = str(tmp_path / "repo")
    import os
    os.makedirs(repo)
    # Server bind on 0.0.0.0 is deterministic evidence of INTERNET_FACING
    code = """
import uvicorn
from fastapi import FastAPI
app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""
    with open(os.path.join(repo, "server.py"), "w") as f:
        f.write(code)

    res = run_pipeline(repo, "test_exposure", allowed_root=repo)
    g = res["graph"]
    file_node = "test_exposure:server.py"

    # 1. Verify Endpoint Node
    endpoints = [data for _, data in g.nodes(data=True) if data.get("category") == "endpoint"]
    assert len(endpoints) >= 1
    assert any(ep.get("network_exposure") == "INTERNET_FACING" for ep in endpoints)

    # 2. Verify Graph Edge (File CALLS Endpoint per Synopsis 5.3)
    calls_edges = [
        (u, v, d) for u, v, d in g.edges(data=True)
        if u == file_node and d.get("relationship") == "CALLS"
    ]
    assert len(calls_edges) >= 1

    # 3. Verify Risk-Factor Extraction
    scores = res["scores"]
    file_score = next(s for s in scores if s["asset_id"] == file_node)
    exposure_factor = file_score["factors"]["internet_exposure"]
    assert exposure_factor["value"] == 1.0
    assert "internet-facing" in exposure_factor["source"].lower()

    # 4. Final score includes internet_exposure
    assert file_score["score"] is not None
    assert "internet_exposure" not in file_score["missing_factors"]


def test_library_centrality_known_topology():
    """
    Constructs a known 5-node graph with 2 libraries and 3 files:
    Formula: in_degree / (total_nodes - 1).
    Total nodes = 5, denominator = 4.
    lib_central has in-degree 3 (imported by file1, file2, file3) -> centrality = 3/4 = 0.75.
    lib_leaf has in-degree 1 (imported by file1 only) -> centrality = 1/4 = 0.25.
    File nodes must return value=None (Not applicable).
    """
    from src.risk.centrality import calculate_in_degree_centrality
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="file2", category="file"))
    ag.add_node(GraphNode(id="file3", category="file"))
    ag.add_node(GraphNode(id="lib_central", category="library"))
    ag.add_node(GraphNode(id="lib_leaf", category="library"))

    ag.add_edge(GraphEdge(source_id="file1", target_id="lib_central", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="file2", target_id="lib_central", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="file3", target_id="lib_central", relationship="IMPORTS"))
    ag.add_edge(GraphEdge(source_id="file1", target_id="lib_leaf", relationship="IMPORTS"))

    c_central = calculate_in_degree_centrality(ag, "lib_central")
    c_leaf = calculate_in_degree_centrality(ag, "lib_leaf")
    c_file = calculate_in_degree_centrality(ag, "file1")

    assert c_central.value == 0.75, f"Expected 0.75, got {c_central.value}"
    assert c_central.confidence == 1.0
    assert c_leaf.value == 0.25, f"Expected 0.25, got {c_leaf.value}"
    assert c_leaf.confidence == 1.0
    assert c_file.value is None, f"Non-library node must have None centrality, got {c_file.value}"
    assert "Not applicable" in c_file.source


def test_mixed_crypto_usages_handling():
    """
    When a file contains BOTH recognized and unrecognized cryptographic findings:
    - The recognized crypto must be rated according to its strength.
    - The unrecognized crypto must NOT be treated as safe (0.0).
    - If recognized crypto is present (e.g. SHA-256 = 0.1), crypto_weakness takes the recognized score.
    - But if only unrecognized crypto exists, crypto_weakness remains None.
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file"))
    ag.add_node(GraphNode(id="cu_sha256", category="crypto_usage", properties={"algorithm": "sha256"}))
    ag.add_node(GraphNode(id="cu_unknown", category="crypto_usage", properties={"algorithm": "custom_obscure_algo"}))

    ag.add_edge(GraphEdge(source_id="file1", target_id="cu_sha256", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file1", target_id="cu_unknown", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file1", {}, {}, {})

    # crypto_weakness evaluates the recognized SHA-256 (0.1) and does not treat custom_obscure_algo as 0.0
    assert factors.crypto_weakness.value == 0.1
    assert "sha256" in factors.crypto_weakness.source.lower()
    # Preserves evidence of unrated crypto in source and penalizes confidence
    assert "unrated crypto also detected: custom_obscure_algo" in factors.crypto_weakness.source
    assert factors.crypto_weakness.confidence == 0.65


def test_mixed_crypto_policy_comparison():
    """
    Compares the 3 policies for mixed recognized/unrecognized crypto:
    1. Naive ignored (understates risk, loses evidence)
    2. Evidence-preserving with epistemic uncertainty discount (active implementation)
    3. Conservative uncertainty floor (pessimistic bound: max(score, 0.5))
    """
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_mixed", category="file"))
    ag.add_node(GraphNode(id="cu_safe", category="crypto_usage", properties={"algorithm": "sha256"}))
    ag.add_node(GraphNode(id="cu_unrated", category="crypto_usage", properties={"algorithm": "proprietary_xor_cipher"}))
    ag.add_edge(GraphEdge(source_id="file_mixed", target_id="cu_safe", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file_mixed", target_id="cu_unrated", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_mixed", {}, {}, {})

    # Active Policy: Evidence-preserving with uncertainty discount
    assert factors.crypto_weakness.value == 0.1
    assert factors.crypto_weakness.confidence == 0.65
    assert "proprietary_xor_cipher" in factors.crypto_weakness.source

    # Conservative Policy comparison
    floor_score = max(factors.crypto_weakness.value, 0.5)
    assert floor_score == 0.5




