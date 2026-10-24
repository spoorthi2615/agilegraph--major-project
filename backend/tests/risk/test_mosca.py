import pytest
from src.risk.mosca import calculate_mosca, MoscaStatus, MoscaUrgency

def test_mosca_at_risk():
    res = calculate_mosca(24, 12, 30)
    assert res.status == MoscaStatus.AT_RISK
    assert res.urgency == MoscaUrgency.AT_RISK
    assert res.total == 36.0
    assert res.urgency_index == 1.2
    assert res.sufficient_data is True
    assert "At Risk" in res.explanation

def test_mosca_urgent_lower_boundary():
    # U = 24 / 30 = 0.80 exactly
    res = calculate_mosca(12, 12, 30)
    assert res.status == MoscaStatus.URGENT
    assert res.urgency == MoscaUrgency.URGENT
    assert res.total == 24.0
    assert res.urgency_index == 0.8
    assert res.sufficient_data is True
    assert "Urgent" in res.explanation

def test_mosca_urgent_upper_boundary():
    # U = 30 / 30 = 1.00 exactly
    res = calculate_mosca(15, 15, 30)
    assert res.status == MoscaStatus.URGENT
    assert res.urgency == MoscaUrgency.URGENT
    assert res.total == 30.0
    assert res.urgency_index == 1.0
    assert res.sufficient_data is True
    assert "Urgent" in res.explanation

def test_mosca_safe_band():
    # U = 21 / 30 = 0.70 < 0.80
    res = calculate_mosca(9, 12, 30)
    assert res.status == MoscaStatus.SAFE
    assert res.urgency == MoscaUrgency.SAFE
    assert res.total == 21.0
    assert res.urgency_index == 0.7
    assert res.sufficient_data is True
    assert "Safe" in res.explanation

def test_mosca_zero_horizon_invalid():
    # z <= 0 is invalid planning assumption
    res = calculate_mosca(0, 0, 0)
    assert res.status == MoscaStatus.INSUFFICIENT_DATA
    assert res.urgency_index is None
    assert res.sufficient_data is False

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

def test_mosca_disclaimer_present():
    res = calculate_mosca(10, 20, 25)
    assert "planning assumption" in res.disclaimer

def test_mosca_deterministic():
    res1 = calculate_mosca(10, 20, 25)
    res2 = calculate_mosca(10, 20, 25)
    assert res1.model_dump() == res2.model_dump()
