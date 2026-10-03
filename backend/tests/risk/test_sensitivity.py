from src.risk.sensitivity import extract_data_sensitivity

def test_sensitivity_known():
    factor = extract_data_sensitivity({"data_classification": "HIGH"})
    assert factor.value == 0.75
    assert factor.confidence == 1.0

def test_sensitivity_unknown():
    factor = extract_data_sensitivity({})
    assert factor.value is None
    assert factor.confidence == 0.0

def test_sensitivity_explicit_unknown():
    factor = extract_data_sensitivity({"data_classification": "UNKNOWN"})
    assert factor.value is None
