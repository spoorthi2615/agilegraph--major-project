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
    exposure_posture: Optional[str] = None
    mosca_provenance: str = "mosca_status is a provided planning input, not automatically discovered evidence."
    sort_key: Tuple[int, float, int, str]

def calculate_migration_priority(
    asset_id: str,
    base_risk: Optional[float],
    mosca_status: MoscaStatus,
    missing_factors: List[str],
    exposure_posture: Optional[str] = None,
    migration_difficulty: Optional[float] = None,
    algorithm: Optional[str] = None
) -> MigrationPriorityResult:
    """
    Calculate the Migration Triage Priority as f(base_risk, mosca_urgency, exposure_posture).
    Downstream planning metric that prioritizes remediation queues without altering
    the objective, scientific risk score.
    """
    if isinstance(mosca_status, str):
        try:
            mosca_status = MoscaStatus(mosca_status)
        except ValueError:
            mosca_status = MoscaStatus.INSUFFICIENT_DATA

    priority_order = {
        PriorityLevel.HIGH: 0,
        PriorityLevel.MEDIUM: 1,
        PriorityLevel.LOW: 2,
        PriorityLevel.NOT_ASSESSED: 3
    }
    mosca_order = {
        MoscaStatus.AT_RISK: 0,
        MoscaStatus.URGENT: 1,
        MoscaStatus.INSUFFICIENT_DATA: 2,
        MoscaStatus.SAFE: 3,
        MoscaStatus.NOT_AT_RISK: 3
    }

    # Informational fields that do NOT affect priority:
    evidence_status = "Complete" if not missing_factors else f"Missing {len(missing_factors)} factors"
    pqc_relevance = True if algorithm in ["rsa", "ecdsa", "ed25519", "dsa"] else False
    if base_risk is not None and base_risk >= 0.7:
        pqc_relevance = True

    is_internet_facing = bool(exposure_posture and str(exposure_posture).upper() == "INTERNET_FACING")
    exp_label = "INTERNET_FACING" if is_internet_facing else (exposure_posture or "INTERNAL/CONTAINED")

    # Triage Matrix: f(base_risk, mosca_urgency, exposure_posture)
    if base_risk is None:
        priority = PriorityLevel.NOT_ASSESSED
        rationale = "Priority cannot be determined due to missing preliminary risk score."
    elif base_risk >= 0.75:
        priority = PriorityLevel.HIGH
        rationale = (
            f"High Priority: Preliminary risk is critical/high ({base_risk:.2f}). "
            f"Mosca urgency: {mosca_status.value}, Exposure posture: {exp_label}."
        )
    elif base_risk >= 0.45:
        # Moderate risk tier
        if mosca_status == MoscaStatus.AT_RISK:
            priority = PriorityLevel.HIGH
            rationale = (
                f"High Priority: Elevated due to AT_RISK planning urgency. "
                f"Preliminary risk remains moderate ({base_risk:.2f})."
            )
        elif mosca_status == MoscaStatus.URGENT:
            if is_internet_facing:
                priority = PriorityLevel.HIGH
                rationale = (
                    f"High Priority: Elevated due to combination of URGENT planning horizon "
                    f"and INTERNET_FACING exposure posture ({base_risk:.2f})."
                )
            else:
                priority = PriorityLevel.MEDIUM
                rationale = (
                    f"Medium Priority: Preliminary risk is moderate ({base_risk:.2f}) "
                    f"under URGENT planning horizon with {exp_label} posture."
                )
        else:
            priority = PriorityLevel.MEDIUM
            rationale = (
                f"Medium Priority: Preliminary risk is moderate ({base_risk:.2f}). "
                f"Mosca planning urgency: {mosca_status.value}."
            )
    else:
        # Low risk tier (< 0.45)
        if mosca_status == MoscaStatus.AT_RISK:
            if is_internet_facing:
                priority = PriorityLevel.HIGH
                rationale = (
                    f"High Priority: Elevated from low base risk ({base_risk:.2f}) "
                    f"due to AT_RISK planning urgency and INTERNET_FACING exposure."
                )
            else:
                priority = PriorityLevel.MEDIUM
                rationale = (
                    f"Medium Priority: Elevated due to AT_RISK planning urgency. "
                    f"Preliminary risk remains low ({base_risk:.2f})."
                )
        elif mosca_status == MoscaStatus.URGENT:
            if is_internet_facing:
                priority = PriorityLevel.MEDIUM
                rationale = (
                    f"Medium Priority: Elevated from low risk due to INTERNET_FACING "
                    f"exposure under URGENT planning horizon."
                )
            else:
                priority = PriorityLevel.LOW
                rationale = (
                    f"Low Priority: Preliminary risk is low ({base_risk:.2f}) "
                    f"and exposure is contained despite URGENT planning horizon."
                )
        else:
            priority = PriorityLevel.LOW
            rationale = (
                f"Low Priority: Preliminary risk is low ({base_risk:.2f}) "
                f"and Mosca is {mosca_status.value}."
            )

    # Tie-breaking sort key: Priority -> -Risk -> Mosca -> Asset ID
    sort_key = (
        priority_order[priority],
        -base_risk if base_risk is not None else 0.0,
        mosca_order.get(mosca_status, 3),
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
        exposure_posture=exposure_posture,
        mosca_provenance="mosca_status is a provided planning input, not automatically discovered evidence.",
        sort_key=sort_key
    )
