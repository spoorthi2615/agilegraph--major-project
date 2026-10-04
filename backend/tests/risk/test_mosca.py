import pytest
from src.risk.mosca import calculate_mosca, MoscaStatus

def test_mosca_at_risk():
    res = calculate_mosca(24, 12, 30)
    assert res.status == MoscaStatus.AT_RISK
    assert res.total == 36
    assert res.sufficient_data is True

def test_mosca_not_at_risk():
    res = calculate_mosca(12, 12, 30)
    assert res.status == MoscaStatus.NOT_AT_RISK
    assert res.total == 24
    assert res.sufficient_data is True

def test_mosca_equality():
    res = calculate_mosca(15, 15, 30)
    assert res.status == MoscaStatus.NOT_AT_RISK
    assert res.total == 30

def test_mosca_zero_values():
    res = calculate_mosca(0, 0, 0)
    assert res.status == MoscaStatus.NOT_AT_RISK
    assert res.total == 0

def test_mosca_missing_x():
    res = calculate_mosca(None, 12, 30)
    assert res.status == MoscaStatus.INSUFFICIENT_DATA
    assert res.sufficient_data is False

def test_mosca_missing_y():
    res = calculate_mosca(12, None, 30)
    assert res.status == MoscaStatus.INSUFFICIENT_DATA
    assert res.sufficient_data is False

def test_mosca_missing_z():
    res = calculate_mosca(12, 12, None)
    assert res.status == MoscaStatus.INSUFFICIENT_DATA
    assert res.sufficient_data is False

def test_mosca_invalid_negative():
    res = calculate_mosca(-1, 12, 30)
    assert res.status == MoscaStatus.INSUFFICIENT_DATA
    assert res.sufficient_data is False
    assert "negative" in res.explanation

def test_mosca_deterministic():
    res1 = calculate_mosca(10, 20, 25)
    res2 = calculate_mosca(10, 20, 25)
    assert res1.model_dump() == res2.model_dump()
