from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone

class MigrationLifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATED = "EVALUATED"
    IN_PLANNING = "IN_PLANNING"
    IN_MIGRATION = "IN_MIGRATION"
    VALIDATED = "VALIDATED"
    DECOMMISSIONED = "DECOMMISSIONED"

# Backward-compatible alias
RoadmapState = MigrationLifecycleState

# Canonical state transitions per Synopsis Section 5.6
VALID_TRANSITIONS: Dict[MigrationLifecycleState, List[MigrationLifecycleState]] = {
    MigrationLifecycleState.DISCOVERED: [
        MigrationLifecycleState.EVALUATED,
        MigrationLifecycleState.DECOMMISSIONED,  # Dead/unused crypto removed immediately
    ],
    MigrationLifecycleState.EVALUATED: [
        MigrationLifecycleState.IN_PLANNING,
        MigrationLifecycleState.DECOMMISSIONED,
        MigrationLifecycleState.DISCOVERED,      # Rescan/reset
    ],
    MigrationLifecycleState.IN_PLANNING: [
        MigrationLifecycleState.IN_MIGRATION,
        MigrationLifecycleState.EVALUATED,       # Plan deferred/cancelled
    ],
    MigrationLifecycleState.IN_MIGRATION: [
        MigrationLifecycleState.VALIDATED,
        MigrationLifecycleState.IN_PLANNING,     # Rollback to planning
    ],
    MigrationLifecycleState.VALIDATED: [
        MigrationLifecycleState.DECOMMISSIONED,  # Legacy crypto retired
        MigrationLifecycleState.IN_MIGRATION,    # Regression discovered post-validation
    ],
    MigrationLifecycleState.DECOMMISSIONED: [
        MigrationLifecycleState.DISCOVERED,      # Resurrected or re-introduced
        MigrationLifecycleState.IN_PLANNING,
    ]
}

LEGACY_STATE_MAPPING: Dict[str, MigrationLifecycleState] = {
    "NOT_ASSESSED": MigrationLifecycleState.DISCOVERED,
    "ASSESSMENT_REQUIRED": MigrationLifecycleState.DISCOVERED,
    "MIGRATION_CANDIDATE": MigrationLifecycleState.EVALUATED,
    "HIGH_PRIORITY": MigrationLifecycleState.EVALUATED,
    "PLANNED": MigrationLifecycleState.IN_PLANNING,
    "IN_PROGRESS": MigrationLifecycleState.IN_MIGRATION,
    "MIGRATED": MigrationLifecycleState.VALIDATED,
    "VERIFIED": MigrationLifecycleState.VALIDATED,
}

def parse_lifecycle_state(val: str | MigrationLifecycleState) -> MigrationLifecycleState:
    if isinstance(val, MigrationLifecycleState):
        return val
    str_val = str(val).strip().upper()
    if str_val in MigrationLifecycleState.__members__:
        return MigrationLifecycleState[str_val]
    if str_val in LEGACY_STATE_MAPPING:
        return LEGACY_STATE_MAPPING[str_val]
    raise ValueError(f"Unknown lifecycle state: {val}")

class MigrationStateRecord(BaseModel):
    asset_id: str
    current_state: MigrationLifecycleState = MigrationLifecycleState.DISCOVERED
    previous_state: Optional[MigrationLifecycleState] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def is_transition_allowed(
    current: MigrationLifecycleState | str, 
    requested: MigrationLifecycleState | str
) -> bool:
    """Check if a transition from current state to requested state is valid."""
    try:
        curr_enum = parse_lifecycle_state(current)
        req_enum = parse_lifecycle_state(requested)
    except ValueError:
        return False
        
    if curr_enum == req_enum:
        return True  # Same-state transitions are allowed (no-op)
    
    return req_enum in VALID_TRANSITIONS.get(curr_enum, [])

def transition_state(
    record: MigrationStateRecord, 
    requested: MigrationLifecycleState | str,
    reason: Optional[str] = None,
    operator: Optional[str] = None
) -> MigrationStateRecord:
    """
    Attempt to transition the migration state record to the requested state.
    Raises ValueError if the transition is invalid.
    """
    req_enum = parse_lifecycle_state(requested)
    
    if not is_transition_allowed(record.current_state, req_enum):
        raise ValueError(
            f"Invalid state transition. "
            f"Cannot transition from {record.current_state.value} to {req_enum.value}. "
            f"Allowed transitions: {[s.value for s in VALID_TRANSITIONS.get(record.current_state, [])]}"
        )
    
    if record.current_state == req_enum:
        return record
        
    return MigrationStateRecord(
        asset_id=record.asset_id,
        current_state=req_enum,
        previous_state=record.current_state,
        updated_at=datetime.now(timezone.utc)
    )
