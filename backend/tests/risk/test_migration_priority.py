import pytest
from src.risk.mosca import MoscaStatus
from src.risk.migration_priority import calculate_migration_priority, PriorityLevel

def test_same_input_same_priority():
    res1 = calculate_migration_priority("asset1", 0.6, MoscaStatus.AT_RISK, [])
    res2 = calculate_migration_priority("asset1", 0.6, MoscaStatus.AT_RISK, [])
    assert res1.model_dump() == res2.model_dump()

def test_missing_evidence():
    res = calculate_migration_priority("asset1", None, MoscaStatus.INSUFFICIENT_DATA, ["crypto_weakness"])
    assert res.priority == PriorityLevel.NOT_ASSESSED
    assert res.evidence_status == "Missing 1 factors"

def test_informational_fields_do_not_change_priority():
    res1 = calculate_migration_priority("A", 0.4, MoscaStatus.NOT_AT_RISK, [], migration_difficulty=0.9, algorithm="rsa")
    res2 = calculate_migration_priority("A", 0.4, MoscaStatus.NOT_AT_RISK, ["data_sensitivity"], migration_difficulty=None, algorithm="unknown")
    assert res1.priority == res2.priority
    assert res1.priority == PriorityLevel.LOW

def test_mosca_planning_urgency_elevates_priority_without_changing_risk():
    res_base = calculate_migration_priority("A", 0.6, MoscaStatus.NOT_AT_RISK, [])
    assert res_base.priority == PriorityLevel.MEDIUM
    assert res_base.risk_score == 0.6

    res_elevated = calculate_migration_priority("A", 0.6, MoscaStatus.AT_RISK, [])
    assert res_elevated.priority == PriorityLevel.HIGH
    assert res_elevated.risk_score == 0.6  # Risk score MUST remain unchanged
    assert "Elevated due to AT_RISK planning urgency" in res_elevated.rationale

def test_mosca_planning_urgency_on_low_risk():
    res_base = calculate_migration_priority("A", 0.3, MoscaStatus.NOT_AT_RISK, [])
    assert res_base.priority == PriorityLevel.LOW

    res_elevated = calculate_migration_priority("A", 0.3, MoscaStatus.AT_RISK, [])
    assert res_elevated.priority == PriorityLevel.MEDIUM
    assert res_elevated.risk_score == 0.3  # Risk score MUST remain unchanged

def test_critical_risk_is_high_regardless_of_mosca():
    res = calculate_migration_priority("A", 0.9, MoscaStatus.NOT_AT_RISK, [])
    assert res.priority == PriorityLevel.HIGH
    assert res.risk_score == 0.9

def test_deterministic_ordering_and_tie_breaking():
    # Tie breaking is: Priority -> -Risk -> Mosca -> Asset ID
    assets = [
        calculate_migration_priority("C", 0.6, MoscaStatus.AT_RISK, []),        # HIGH (0.6, AT_RISK)
        calculate_migration_priority("A", 0.9, MoscaStatus.NOT_AT_RISK, []),    # HIGH (0.9, NOT_AT_RISK)
        calculate_migration_priority("B", 0.9, MoscaStatus.NOT_AT_RISK, []),    # HIGH (0.9, NOT_AT_RISK)
        calculate_migration_priority("D", 0.4, MoscaStatus.NOT_AT_RISK, []),    # LOW (0.4, NOT_AT_RISK)
        calculate_migration_priority("E", 0.4, MoscaStatus.AT_RISK, [])         # MEDIUM (0.4, AT_RISK)
    ]
    assets_sorted = sorted(assets, key=lambda x: x.sort_key)
    
    assert assets_sorted[0].sort_key[-1] == "A" # HIGH, 0.9, A
    assert assets_sorted[1].sort_key[-1] == "B" # HIGH, 0.9, B
    assert assets_sorted[2].sort_key[-1] == "C" # HIGH, 0.6, C
    assert assets_sorted[3].sort_key[-1] == "E" # MEDIUM, 0.4, E
    assert assets_sorted[4].sort_key[-1] == "D" # LOW, 0.4, D
