from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class MoscaStatus(str, Enum):
    AT_RISK = "AT_RISK"
    URGENT = "URGENT"
    SAFE = "SAFE"
    NOT_AT_RISK = "NOT_AT_RISK"  # Backward-compatible alias for SAFE
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

MoscaUrgency = MoscaStatus

class MoscaResult(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    total: Optional[float] = None
    urgency_index: Optional[float] = Field(None, description="Mosca readiness index U = (x + y) / z")
    status: MoscaStatus
    urgency: MoscaStatus
    explanation: str
    sufficient_data: bool
    unit: str = "months"
    disclaimer: str = (
        "Quantum capability horizon z is an organizational planning assumption, "
        "not a physical quantum prediction."
    )

def calculate_mosca(
    x_months: Optional[float], 
    y_months: Optional[float], 
    z_months: Optional[float]
) -> MoscaResult:
    """
    Calculate the Mosca Readiness Index: U = (x + y) / z
    x = data confidentiality shelf-life / retention period
    y = migration timeline to quantum-safe alternatives
    z = quantum capability horizon (configurable planning assumption, not a physical prediction)
    
    Urgency Bands:
      - U > 1.0:           AT_RISK  (Shelf-life + migration time exceeds quantum horizon)
      - 0.8 <= U <= 1.0:   URGENT   (Approaching quantum horizon within 20% safety margin)
      - U < 0.8:           SAFE     (Sufficient safety margin before quantum horizon)
      - Missing or z <= 0: INSUFFICIENT_DATA
    """
    if x_months is None or y_months is None or z_months is None:
        return MoscaResult(
            x=x_months,
            y=y_months,
            z=z_months,
            total=None,
            urgency_index=None,
            status=MoscaStatus.INSUFFICIENT_DATA,
            urgency=MoscaStatus.INSUFFICIENT_DATA,
            explanation="Missing required inputs (x, y, or z) to calculate Mosca status.",
            sufficient_data=False
        )

    if x_months < 0 or y_months < 0 or z_months <= 0:
        msg = "Inputs x and y cannot be negative, and z must be strictly greater than 0."
        return MoscaResult(
            x=x_months,
            y=y_months,
            z=z_months,
            total=None,
            urgency_index=None,
            status=MoscaStatus.INSUFFICIENT_DATA,
            urgency=MoscaStatus.INSUFFICIENT_DATA,
            explanation=msg,
            sufficient_data=False
        )
        
    total = float(x_months + y_months)
    u = total / float(z_months)
    u_rounded = round(u, 4)

    if u > 1.0:
        status = MoscaStatus.AT_RISK
        explanation = (
            f"At Risk (U = {u:.2f} > 1.0): Data retention ({x_months:g}) + "
            f"migration time ({y_months:g}) exceeds quantum horizon ({z_months:g})."
        )
    elif u >= 0.8:
        status = MoscaStatus.URGENT
        explanation = (
            f"Urgent (0.8 <= U = {u:.2f} <= 1.0): Data retention ({x_months:g}) + "
            f"migration time ({y_months:g}) approaches quantum horizon ({z_months:g}) within safety margin."
        )
    else:
        status = MoscaStatus.SAFE
        explanation = (
            f"Safe (U = {u:.2f} < 0.8): Data retention ({x_months:g}) + "
            f"migration time ({y_months:g}) is well within quantum horizon ({z_months:g})."
        )
        
    return MoscaResult(
        x=float(x_months),
        y=float(y_months),
        z=float(z_months),
        total=total,
        urgency_index=u_rounded,
        status=status,
        urgency=status,
        explanation=explanation,
        sufficient_data=True
    )
