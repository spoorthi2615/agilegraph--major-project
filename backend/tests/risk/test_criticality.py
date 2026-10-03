from src.risk.criticality import extract_asset_criticality

def test_criticality_known():
    factor = extract_asset_criticality({"business_criticality": "CRITICAL"})
    assert factor.value == 1.0
    assert factor.confidence == 1.0

def test_criticality_unknown():
    factor = extract_asset_criticality({})
    assert factor.value is None
    assert factor.confidence == 0.0
