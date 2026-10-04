from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class RoadmapState(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    ASSESSMENT_REQUIRED = "ASSESSMENT_REQUIRED"
    MIGRATION_CANDIDATE = "MIGRATION_CANDIDATE"
    HIGH_PRIORITY = "HIGH_PRIORITY"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    MIGRATED = "MIGRATED"
    VERIFIED = "VERIFIED"

# Define the valid transition matrix
VALID_TRANSITIONS: Dict[RoadmapState, List[RoadmapState]] = {
    RoadmapState.NOT_ASSESSED: [
        RoadmapState.ASSESSMENT_REQUIRED,
        RoadmapState.MIGRATION_CANDIDATE
    ],
    RoadmapState.ASSESSMENT_REQUIRED: [
        RoadmapState.MIGRATION_CANDIDATE,
        RoadmapState.NOT_ASSESSED
    ],
    RoadmapState.MIGRATION_CANDIDATE: [
        RoadmapState.HIGH_PRIORITY,
        RoadmapState.PLANNED,
        RoadmapState.ASSESSMENT_REQUIRED # Backward reassessment
    ],
    RoadmapState.HIGH_PRIORITY: [
        RoadmapState.PLANNED,
        RoadmapState.MIGRATION_CANDIDATE # Downgrade priority
    ],
    RoadmapState.PLANNED: [
        RoadmapState.IN_PROGRESS,
        RoadmapState.MIGRATION_CANDIDATE # Cancel plan
    ],
    RoadmapState.IN_PROGRESS: [
        RoadmapState.MIGRATED,
        RoadmapState.PLANNED # Revert progress
    ],
    RoadmapState.MIGRATED: [
        RoadmapState.VERIFIED,
        RoadmapState.IN_PROGRESS # Revert to in-progress if migration was incomplete
    ],
    RoadmapState.VERIFIED: [
        RoadmapState.MIGRATED # If verification fails later, fall back to migrated
    ]
}

class MigrationStateRecord(BaseModel):
    asset_id: str
    current_state: RoadmapState = RoadmapState.NOT_ASSESSED
    previous_state: Optional[RoadmapState] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

def is_transition_allowed(current: RoadmapState, requested: RoadmapState) -> bool:
    """Check if a transition from current state to requested state is valid."""
    if current == requested:
        return True # Same-state transitions are allowed (no-op)
    
    return requested in VALID_TRANSITIONS.get(current, [])

def transition_state(record: MigrationStateRecord, requested: RoadmapState) -> MigrationStateRecord:
    """
    Attempt to transition the migration state record to the requested state.
    Raises ValueError if the transition is invalid.
    """
    if not is_transition_allowed(record.current_state, requested):
        raise ValueError(
            f"Invalid state transition. "
            f"Cannot transition from {record.current_state.value} to {requested.value}. "
            f"Allowed transitions: {[s.value for s in VALID_TRANSITIONS.get(record.current_state, [])]}"
        )
    
    if record.current_state == requested:
        return record
        
    return MigrationStateRecord(
        asset_id=record.asset_id,
        current_state=requested,
        previous_state=record.current_state,
        updated_at=datetime.utcnow()
    )
