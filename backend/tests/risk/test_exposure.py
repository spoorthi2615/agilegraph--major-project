from src.risk.exposure import extract_internet_exposure

def test_exposure_known_metadata():
    factor = extract_internet_exposure({"network_exposure": "INTERNET_FACING"})
    assert factor.value == 1.0
    
def test_exposure_inferred_tls():
    factor = extract_internet_exposure({"tls_host": "8.8.8.8"})
    assert factor.value is None
    assert factor.confidence == 0.0
    assert "insufficient evidence" in factor.source
    
def test_exposure_unknown():
    factor = extract_internet_exposure({"tls_host": "localhost"})
    assert factor.value is None
    assert factor.confidence == 0.0
