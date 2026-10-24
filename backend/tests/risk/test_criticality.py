from src.risk.criticality import extract_asset_criticality

def test_criticality_known():
    factor = extract_asset_criticality({"business_criticality": "CRITICAL"})
    assert factor.value == 1.0
    assert factor.confidence == 1.0

    factor_med = extract_asset_criticality({"service_criticality": "MEDIUM"})
    assert factor_med.value == 0.5
    assert factor_med.confidence == 1.0

def test_criticality_unknown():
    factor = extract_asset_criticality({})
    assert factor.value is None
    assert factor.confidence == 0.0

def test_criticality_path_proxies():
    # Non-production test and example files
    f_test = extract_asset_criticality({}, file_path="tests/test_signature.py")
    assert f_test.value == 0.25
    assert "test/example proxy" in f_test.source

    f_example = extract_asset_criticality({}, file_path="examples/basic_signing.py")
    assert f_example.value == 0.25
    assert "test/example proxy" in f_example.source

    # Security-critical modules
    f_sec = extract_asset_criticality({}, file_path="src/crypto/aes_engine.py")
    assert f_sec.value == 0.75
    assert "security-critical module proxy" in f_sec.source

    f_jwt = extract_asset_criticality({}, file_path="auth/jwt_validator.go")
    assert f_jwt.value == 0.75

    # Shared utility module by in-degree
    f_shared = extract_asset_criticality({}, file_path="src/common/core.py", in_degree=4)
    assert f_shared.value == 0.50
    assert "shared dependency module proxy" in f_shared.source

def test_criticality_ordinary_utility_remains_uncertain():
    # Ordinary helper file with low in-degree and no security role: must remain None
    f_util = extract_asset_criticality({}, file_path="src/utils/text_formatter.py", in_degree=1)
    assert f_util.value is None
    assert f_util.confidence == 0.0
    assert f_util.source == "not provided"

def test_criticality_unintended_category_remains_none():
    # Metadata for a Library or Endpoint node without file path or explicit criticality
    endpoint_meta = {"path": "/healthz", "method": "GET"}
    f_ep = extract_asset_criticality(endpoint_meta)
    assert f_ep.value is None
    assert f_ep.confidence == 0.0
