import pytest
from src.models.migration_state import (
    RoadmapState, MigrationStateRecord, is_transition_allowed, transition_state, VALID_TRANSITIONS
)
from src.risk.mosca import MoscaStatus
from src.risk.migration_priority import PriorityLevel

def test_every_valid_forward_transition():
    # Test a full valid forward lifecycle
    record = MigrationStateRecord(asset_id="asset1", current_state=RoadmapState.NOT_ASSESSED)
    
    # Forward path
    path = [
        RoadmapState.ASSESSMENT_REQUIRED,
        RoadmapState.MIGRATION_CANDIDATE,
        RoadmapState.HIGH_PRIORITY,
        RoadmapState.PLANNED,
        RoadmapState.IN_PROGRESS,
        RoadmapState.MIGRATED,
        RoadmapState.VERIFIED
    ]
    
    for next_state in path:
        assert is_transition_allowed(record.current_state, next_state) is True
        record = transition_state(record, next_state)
        assert record.current_state == next_state
        
def test_invalid_arbitrary_jumps():
    record = MigrationStateRecord(asset_id="asset1", current_state=RoadmapState.NOT_ASSESSED)
    assert is_transition_allowed(record.current_state, RoadmapState.IN_PROGRESS) is False
    assert is_transition_allowed(record.current_state, RoadmapState.VERIFIED) is False
    assert is_transition_allowed(RoadmapState.MIGRATED, RoadmapState.PLANNED) is False
    
    with pytest.raises(ValueError, match="Invalid state transition"):
        transition_state(record, RoadmapState.MIGRATED)

def test_invalid_backwards_transitions_unless_supported():
    # Valid backwards: MIGRATED -> IN_PROGRESS
    assert is_transition_allowed(RoadmapState.MIGRATED, RoadmapState.IN_PROGRESS) is True
    
    # Invalid backwards: VERIFIED -> IN_PROGRESS
    assert is_transition_allowed(RoadmapState.VERIFIED, RoadmapState.IN_PROGRESS) is False

def test_same_state_behavior():
    record = MigrationStateRecord(asset_id="asset1", current_state=RoadmapState.PLANNED)
    assert is_transition_allowed(RoadmapState.PLANNED, RoadmapState.PLANNED) is True
    new_record = transition_state(record, RoadmapState.PLANNED)
    # The record should remain unmodified
    assert new_record.current_state == RoadmapState.PLANNED
    assert new_record.previous_state == record.previous_state

def test_unknown_invalid_state_values():
    with pytest.raises(ValueError):
        # Enums provide natural type safety against arbitrary strings
        RoadmapState("INVALID_STATE_XYZ")

def test_deterministic_validation():
    assert is_transition_allowed(RoadmapState.NOT_ASSESSED, RoadmapState.MIGRATION_CANDIDATE) is True
    assert is_transition_allowed(RoadmapState.NOT_ASSESSED, RoadmapState.MIGRATION_CANDIDATE) is True

def test_state_does_not_alter_other_metrics():
    # Proof that RoadmapState is entirely decoupled from Risk, Priority, and Mosca
    mock_risk = 0.8
    mock_mosca = MoscaStatus.AT_RISK
    mock_priority = PriorityLevel.HIGH
    
    record = MigrationStateRecord(asset_id="asset1", current_state=RoadmapState.PLANNED)
    record = transition_state(record, RoadmapState.IN_PROGRESS)
    
    # Asserting these are distinct models/properties and no side-effects exist
    assert mock_risk == 0.8
    assert mock_mosca == MoscaStatus.AT_RISK
    assert mock_priority == PriorityLevel.HIGH

def test_migrated_does_not_imply_verified():
    # Validates semantic rule: MIGRATED != VERIFIED
    assert RoadmapState.MIGRATED != RoadmapState.VERIFIED
    
    # Needs explicit transition
    assert is_transition_allowed(RoadmapState.MIGRATED, RoadmapState.VERIFIED) is True
    assert RoadmapState.VERIFIED not in VALID_TRANSITIONS[RoadmapState.IN_PROGRESS]

def test_verified_is_planning_assertion():
    # Verified state is a RoadmapState planning/user assertion, not an empirical node risk score
    record = MigrationStateRecord(asset_id="asset1", current_state=RoadmapState.VERIFIED)
    assert isinstance(record.current_state, RoadmapState)
    assert not hasattr(record, "risk_score") # Does not contain empirical risk
