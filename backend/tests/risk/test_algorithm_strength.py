from src.risk.algorithm_strength import extract_crypto_weakness

def test_extract_crypto_weakness_vulnerable():
    factor = extract_crypto_weakness("rsa")
    assert factor.value == 0.9
    assert "algorithm classification" in factor.source

def test_extract_crypto_weakness_strong():
    factor = extract_crypto_weakness("kyber")
    assert factor.value == 0.0

def test_extract_crypto_weakness_unknown():
    factor = extract_crypto_weakness("magic_crypto")
    assert factor.value is None
    assert factor.confidence == 0.0

def test_extract_crypto_weakness_none():
    factor = extract_crypto_weakness(None)
    assert factor.value is None
