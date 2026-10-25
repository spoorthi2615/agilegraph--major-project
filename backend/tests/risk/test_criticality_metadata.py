import pytest
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode
from src.risk.factor_extractor import FactorExtractor
from src.risk.criticality import extract_asset_criticality


def test_security_critical_module_path_reaches_extractor():
    """Verifies that a security-critical path reaches the extractor and receives 0.75."""
    ag = AgileGraph()
    node = GraphNode(
        id="cryptography:hazmat/primitives/ciphers/aes.py",
        category="file",
        properties={"file": "hazmat/primitives/ciphers/aes.py", "repository": "cryptography"}
    )
    ag.add_node(node)
    
    extractor = FactorExtractor(ag)
    node_data = ag.G.nodes["cryptography:hazmat/primitives/ciphers/aes.py"]
    
    factors = extractor.extract("cryptography:hazmat/primitives/ciphers/aes.py", node_data, {}, {})
    assert factors.asset_criticality.value == 0.75
    assert "inferred security-critical module proxy" in factors.asset_criticality.source
    assert factors.asset_criticality.confidence == 0.8


def test_recognized_security_path_go():
    """Verifies Go crypto signing/rsa path receives 0.75."""
    ag = AgileGraph()
    node = GraphNode(
        id="go_crypto:crypto/rsa/rsa.go",
        category="file",
        properties={"file": "crypto/rsa/rsa.go", "repository": "go_crypto"}
    )
    ag.add_node(node)
    
    extractor = FactorExtractor(ag)
    node_data = ag.G.nodes["go_crypto:crypto/rsa/rsa.go"]
    
    factors = extractor.extract("go_crypto:crypto/rsa/rsa.go", node_data, {}, {})
    assert factors.asset_criticality.value == 0.75


def test_test_fixture_path_receives_non_production_proxy():
    """Verifies that non-production test fixtures receive 0.25 criticality proxy."""
    ag = AgileGraph()
    node = GraphNode(
        id="project:tests/test_ciphers.py",
        category="file",
        properties={"file": "tests/test_ciphers.py", "repository": "project"}
    )
    ag.add_node(node)
    
    extractor = FactorExtractor(ag)
    node_data = ag.G.nodes["project:tests/test_ciphers.py"]
    
    factors = extractor.extract("project:tests/test_ciphers.py", node_data, {}, {})
    assert factors.asset_criticality.value == 0.25
    assert "inferred non-production asset" in factors.asset_criticality.source


def test_truly_missing_metadata_remains_none():
    """Verifies that generic files without security markers and with low in-degree remain explicitly None."""
    ag = AgileGraph()
    node = GraphNode(
        id="project:utils/helper.py",
        category="file",
        properties={"file": "utils/helper.py", "repository": "project"}
    )
    ag.add_node(node)
    
    extractor = FactorExtractor(ag)
    node_data = ag.G.nodes["project:utils/helper.py"]
    
    factors = extractor.extract("project:utils/helper.py", node_data, {}, {})
    assert factors.asset_criticality.value is None
    assert factors.asset_criticality.confidence == 0.0
    assert factors.asset_criticality.source == "not provided"


def test_fallback_file_path_from_node_attributes_when_empty_metadata_passed():
    """
    Regression test for the build_corpus metadata passing bug:
    Verifies that even if metadata={} is passed to extract(), the extractor
    recovers the file path directly from the graph node attributes.
    """
    ag = AgileGraph()
    node = GraphNode(
        id="cryptography:hazmat/primitives/asymmetric/rsa.py",
        category="file",
        properties={"file": "hazmat/primitives/asymmetric/rsa.py", "repository": "cryptography"}
    )
    ag.add_node(node)
    
    extractor = FactorExtractor(ag)
    # Passing empty metadata={} must NOT cause file_path to be lost!
    factors = extractor.extract("cryptography:hazmat/primitives/asymmetric/rsa.py", {}, {}, {})
    assert factors.asset_criticality.value == 0.75
