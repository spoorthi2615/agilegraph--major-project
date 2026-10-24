import pytest
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.graph.builder import GraphBuilder
from src.scanners.common.models import FindingRecord
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.common.enums import AssetType, Language

def test_graph_contains_all_six_node_types_and_relationships():
    ag = AgileGraph()
    builder = GraphBuilder(ag)

    findings = [
        # 1. CryptoUsage
        FindingRecord(
            asset_type=AssetType.CRYPTO_USAGE,
            repository="test-repo",
            file="auth.py",
            line=15,
            language=Language.PYTHON,
            library="cryptography",
            api="rsa.generate_private_key",
            algorithm="rsa",
            operation="key_generation",
            evidence="generate_private_key()",
            confidence=1.0,
            extra={"key_size": 2048}
        ),
        # 2. Library
        FindingRecord(
            asset_type=AssetType.LIBRARY,
            repository="test-repo",
            file="auth.py",
            line=2,
            language=Language.PYTHON,
            library="cryptography",
            evidence="import cryptography",
            confidence=1.0
        ),
        # 3. Certificate
        FindingRecord(
            asset_type=AssetType.CERTIFICATE,
            repository="test-repo",
            file="auth.py",
            line=8,
            algorithm="rsa",
            evidence="Certificate X.509",
            confidence=0.9,
            extra={"key_size": 2048}
        ),
        # 4. Endpoint
        FindingRecord(
            asset_type=AssetType.ENDPOINT,
            repository="test-repo",
            file="auth.py",
            line=25,
            language=Language.PYTHON,
            api="route:POST:/api/v1/login",
            operation="endpoint_declaration",
            evidence="@app.post('/api/v1/login')",
            confidence=0.95,
            extra={"path": "/api/v1/login", "method": "POST", "protocol": "HTTPS", "network_exposure": "INTERNET_FACING"}
        ),
        # 5. SensitiveData
        FindingRecord(
            asset_type=AssetType.SENSITIVE_DATA,
            repository="test-repo",
            file="auth.py",
            line=12,
            language=Language.PYTHON,
            api="data:user_password",
            operation="sensitive_data_declaration",
            evidence="user_password = ...",
            confidence=0.9,
            extra={"name": "user_password", "classification": "CRITICAL"}
        ),
        # 6. DependencyRecord for manifest dependency
        DependencyRecord(
            repository="test-repo",
            manifest_file="requirements.txt",
            language=Language.PYTHON,
            package_name="cryptography",
            version="41.0.0",
            ecosystem="pypi",
            direct=True,
            evidence="cryptography==41.0.0",
            confidence=1.0
        )
    ]

    builder.build_from_normalized_records(findings)
    g = ag.G

    # Verify all six node categories are present
    categories = {data.get("category") for _, data in g.nodes(data=True)}
    assert "file" in categories, "File node category must be present"
    assert "crypto_usage" in categories, "CryptoUsage node category must be present"
    assert "library" in categories, "Library node category must be present"
    assert "certificate" in categories, "Certificate node category must be present"
    assert "endpoint" in categories, "Endpoint node category must be present"
    assert "sensitive_data" in categories, "SensitiveData node category must be present"

    # Explicitly verify every relationship type with source category, target category, and evidence
    edge_tuples = []
    for u, v, d in g.edges(data=True):
        u_cat = g.nodes[u].get("category")
        v_cat = g.nodes[v].get("category")
        rel = d.get("relationship")
        edge_tuples.append((u_cat, rel, v_cat))

    # 1. CONTAINS: File -> CryptoUsage, File -> Certificate, File -> SensitiveData
    assert ("file", "CONTAINS", "crypto_usage") in edge_tuples
    assert ("file", "CONTAINS", "certificate") in edge_tuples
    assert ("file", "CONTAINS", "sensitive_data") in edge_tuples

    # 2. IMPORTS: File -> Library
    assert ("file", "IMPORTS", "library") in edge_tuples

    # 3. CALLS: File -> Endpoint
    assert ("file", "CALLS", "endpoint") in edge_tuples

    # 4. USES_CERT: CryptoUsage -> Certificate and Endpoint -> Certificate
    assert ("crypto_usage", "USES_CERT", "certificate") in edge_tuples
    assert ("endpoint", "USES_CERT", "certificate") in edge_tuples

    # 5. EXPOSES: Endpoint -> CryptoUsage
    assert ("endpoint", "EXPOSES", "crypto_usage") in edge_tuples

    # 6. PROTECTS: CryptoUsage -> SensitiveData
    assert ("crypto_usage", "PROTECTS", "sensitive_data") in edge_tuples

    # 7. DEPENDS_ON: File (manifest) -> Library
    assert ("file", "DEPENDS_ON", "library") in edge_tuples

    # Assert complete schema legality and zero validation errors
    errors = ag.validate_integrity()
    assert errors == [], f"Validation errors found: {errors}"


def test_validation_rejects_unsupported_relationships():
    """Confirms that graph validation strictly rejects any undeclared edge relationship."""
    from src.graph.validation import validate_graph
    from src.graph.schema import GraphEdge
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file1", category="file", properties={"file": "test.py"}))
    ag.add_node(GraphNode(id="lib1", category="library"))

    # Valid relationship passes
    ag.add_edge(GraphEdge(source_id="file1", target_id="lib1", relationship="IMPORTS"))
    errors = validate_graph(ag)
    assert len(errors) == 0

    # Unsupported relationship fails
    ag.add_edge(GraphEdge(source_id="file1", target_id="lib1", relationship="INVALID_UNDECLARED_REL"))
    errors_invalid = validate_graph(ag)
    assert any("has invalid relationship: INVALID_UNDECLARED_REL" in err for err in errors_invalid)


