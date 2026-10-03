import json
from src.risk.score import RiskScoreResult

def serialize_audit_log(result: RiskScoreResult) -> str:
    """
    Serializes a RiskScoreResult into machine-readable JSON for audit logging.
    """
    return result.model_dump_json(indent=2)
