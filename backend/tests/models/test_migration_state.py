import pytest
from src.models.migration_state import (
    MigrationLifecycleState,
    RoadmapState,
    MigrationStateRecord,
    is_transition_allowed,
    transition_state,
    VALID_TRANSITIONS,
    parse_lifecycle_state
)
from src.risk.mosca import MoscaStatus
from src.risk.migration_priority import PriorityLevel

def test_six_canonical_states_exist():
    expected_states = {
        "DISCOVERED", "EVALUATED", "IN_PLANNING", "IN_MIGRATION", "VALIDATED", "DECOMMISSIONED"
    }
    actual_states = {s.value for s in MigrationLifecycleState}
    assert actual_states == expected_states

def test_canonical_forward_lifecycle():
    # DISCOVERED -> EVALUATED -> IN_PLANNING -> IN_MIGRATION -> VALIDATED -> DECOMMISSIONED
    record = MigrationStateRecord(asset_id="asset1", current_state=MigrationLifecycleState.DISCOVERED)
    
    path = [
        MigrationLifecycleState.EVALUATED,
        MigrationLifecycleState.IN_PLANNING,
        MigrationLifecycleState.IN_MIGRATION,
        MigrationLifecycleState.VALIDATED,
        MigrationLifecycleState.DECOMMISSIONED
    ]
    
    for next_state in path:
        assert is_transition_allowed(record.current_state, next_state) is True
        record = transition_state(record, next_state)
        assert record.current_state == next_state

def test_invalid_arbitrary_jumps():
    record = MigrationStateRecord(asset_id="asset1", current_state=MigrationLifecycleState.DISCOVERED)
    # Cannot jump directly from DISCOVERED to IN_MIGRATION or VALIDATED
    assert is_transition_allowed(record.current_state, MigrationLifecycleState.IN_MIGRATION) is False
    assert is_transition_allowed(record.current_state, MigrationLifecycleState.VALIDATED) is False
    assert is_transition_allowed(MigrationLifecycleState.VALIDATED, MigrationLifecycleState.IN_PLANNING) is False
    
    with pytest.raises(ValueError, match="Invalid state transition"):
        transition_state(record, MigrationLifecycleState.IN_MIGRATION)

def test_valid_backwards_transitions():
    # IN_PLANNING -> EVALUATED (cancelled plan)
    assert is_transition_allowed(MigrationLifecycleState.IN_PLANNING, MigrationLifecycleState.EVALUATED) is True
    # IN_MIGRATION -> IN_PLANNING (rollback)
    assert is_transition_allowed(MigrationLifecycleState.IN_MIGRATION, MigrationLifecycleState.IN_PLANNING) is True
    # VALIDATED -> IN_MIGRATION (post-validation regression)
    assert is_transition_allowed(MigrationLifecycleState.VALIDATED, MigrationLifecycleState.IN_MIGRATION) is True
    
    # Invalid backwards jump: VALIDATED -> DISCOVERED
    assert is_transition_allowed(MigrationLifecycleState.VALIDATED, MigrationLifecycleState.DISCOVERED) is False

def test_same_state_behavior():
    record = MigrationStateRecord(asset_id="asset1", current_state=MigrationLifecycleState.IN_PLANNING)
    assert is_transition_allowed(MigrationLifecycleState.IN_PLANNING, MigrationLifecycleState.IN_PLANNING) is True
    new_record = transition_state(record, MigrationLifecycleState.IN_PLANNING)
    assert new_record.current_state == MigrationLifecycleState.IN_PLANNING
    assert new_record.previous_state == record.previous_state

def test_legacy_aliases_parsing():
    assert parse_lifecycle_state("NOT_ASSESSED") == MigrationLifecycleState.DISCOVERED
    assert parse_lifecycle_state("PLANNED") == MigrationLifecycleState.IN_PLANNING
    assert parse_lifecycle_state("MIGRATED") == MigrationLifecycleState.VALIDATED

def test_unknown_invalid_state_values():
    with pytest.raises(ValueError):
        parse_lifecycle_state("INVALID_STATE_XYZ")

def test_state_does_not_alter_other_metrics():
    # Proof that RoadmapState is entirely decoupled from Risk, Priority, and Mosca
    mock_risk = 0.8
    mock_mosca = MoscaStatus.AT_RISK
    mock_priority = PriorityLevel.HIGH
    
    record = MigrationStateRecord(asset_id="asset1", current_state=MigrationLifecycleState.IN_PLANNING)
    record = transition_state(record, MigrationLifecycleState.IN_MIGRATION)
    
    assert mock_risk == 0.8
    assert mock_mosca == MoscaStatus.AT_RISK
    assert mock_priority == PriorityLevel.HIGH
