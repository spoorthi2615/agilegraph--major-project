from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Tuple
from src.risk.mosca import MoscaStatus

class PriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_ASSESSED = "NOT_ASSESSED"

class MigrationPriorityResult(BaseModel):
    priority: PriorityLevel
    rationale: str
    risk_score: Optional[float]
    evidence_status: str
    pqc_relevance: bool
    migration_difficulty: Optional[float]
    mosca_status: MoscaStatus
    mosca_provenance: str = "mosca_status is a provided planning input, not automatically discovered evidence."
    sort_key: Tuple[int, float, int, str]

def calculate_migration_priority(
    asset_id: str,
    base_risk: Optional[float],
    mosca_status: MoscaStatus,
    missing_factors: List[str],
    migration_difficulty: Optional[float] = None,
    algorithm: Optional[str] = None
) -> MigrationPriorityResult:
    """
    Calculate the Migration Priority as a downstream planning metric.
    Does NOT modify or feed back into the scientific risk score.
    """
    priority_order = {PriorityLevel.HIGH: 0, PriorityLevel.MEDIUM: 1, PriorityLevel.LOW: 2, PriorityLevel.NOT_ASSESSED: 3}
    mosca_order = {MoscaStatus.AT_RISK: 0, MoscaStatus.INSUFFICIENT_DATA: 1, MoscaStatus.NOT_AT_RISK: 2}

    # Informational fields that do NOT affect priority:
    evidence_status = "Complete" if not missing_factors else f"Missing {len(missing_factors)} factors"
    pqc_relevance = True if algorithm in ["rsa", "ecdsa", "ed25519", "dsa"] else False
    if base_risk is not None and base_risk >= 0.7:
        pqc_relevance = True

    # Priority Policy (Option A):
    if base_risk is None:
        priority = PriorityLevel.NOT_ASSESSED
        rationale = "Priority cannot be determined due to missing preliminary risk score."
    elif base_risk >= 0.8:
        priority = PriorityLevel.HIGH
        rationale = f"High Priority: Preliminary risk is critical ({base_risk:.2f}). Mosca planning urgency: {mosca_status.value}."
    elif base_risk >= 0.5 and mosca_status == MoscaStatus.AT_RISK:
        priority = PriorityLevel.HIGH
        rationale = f"High Priority: Elevated due to AT_RISK planning urgency. Preliminary risk remains moderate ({base_risk:.2f})."
    elif base_risk >= 0.5 and mosca_status != MoscaStatus.AT_RISK:
        priority = PriorityLevel.MEDIUM
        rationale = f"Medium Priority: Preliminary risk is moderate ({base_risk:.2f}). Mosca planning urgency: {mosca_status.value}."
    elif base_risk < 0.5 and mosca_status == MoscaStatus.AT_RISK:
        priority = PriorityLevel.MEDIUM
        rationale = f"Medium Priority: Elevated due to AT_RISK planning urgency. Preliminary risk remains low ({base_risk:.2f})."
    else:
        priority = PriorityLevel.LOW
        rationale = f"Low Priority: Preliminary risk is low ({base_risk:.2f}) and Mosca is {mosca_status.value}."

    # Tie-breaking sort key: Priority -> -Risk -> Mosca -> Asset ID
    sort_key = (
        priority_order[priority],
        -base_risk if base_risk is not None else 0.0,
        mosca_order[mosca_status],
        asset_id
    )

    return MigrationPriorityResult(
        priority=priority,
        rationale=rationale,
        risk_score=base_risk,
        evidence_status=evidence_status,
        pqc_relevance=pqc_relevance,
        migration_difficulty=migration_difficulty,
        mosca_status=mosca_status,
        mosca_provenance="mosca_status is a provided planning input, not automatically discovered evidence.",
        sort_key=sort_key
    )
