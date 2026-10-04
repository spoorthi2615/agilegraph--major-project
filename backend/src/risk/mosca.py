from enum import Enum
from pydantic import BaseModel
from typing import Optional

class MoscaStatus(str, Enum):
    AT_RISK = "AT_RISK"
    NOT_AT_RISK = "NOT_AT_RISK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class MoscaResult(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    z: Optional[int] = None
    total: Optional[int] = None
    status: MoscaStatus
    explanation: str
    sufficient_data: bool
    unit: str = "months"

def calculate_mosca(
    x_months: Optional[int], 
    y_months: Optional[int], 
    z_months: Optional[int]
) -> MoscaResult:
    """
    Calculate the Mosca Readiness Index.
    x = data confidentiality period
    y = migration time
    z = quantum capability horizon (configurable planning assumption, not a prediction)
    
    If x + y > z -> AT_RISK
    If x + y <= z -> NOT_AT_RISK
    """
    if x_months is None or y_months is None or z_months is None:
        return MoscaResult(
            x=x_months,
            y=y_months,
            z=z_months,
            total=None,
            status=MoscaStatus.INSUFFICIENT_DATA,
            explanation="Missing required inputs (x, y, or z) to calculate Mosca status.",
            sufficient_data=False
        )

    if x_months < 0 or y_months < 0 or z_months < 0:
        return MoscaResult(
            x=x_months,
            y=y_months,
            z=z_months,
            total=None,
            status=MoscaStatus.INSUFFICIENT_DATA,
            explanation="Inputs x, y, and z cannot be negative.",
            sufficient_data=False
        )
        
    total = x_months + y_months
    if total > z_months:
        status = MoscaStatus.AT_RISK
        explanation = f"At Risk: Data confidentiality period ({x_months}) + migration time ({y_months}) exceeds quantum horizon ({z_months})."
    else:
        status = MoscaStatus.NOT_AT_RISK
        explanation = f"Not At Risk: Data confidentiality period ({x_months}) + migration time ({y_months}) does not exceed quantum horizon ({z_months})."
        
    return MoscaResult(
        x=x_months,
        y=y_months,
        z=z_months,
        total=total,
        status=status,
        explanation=explanation,
        sufficient_data=True
    )
