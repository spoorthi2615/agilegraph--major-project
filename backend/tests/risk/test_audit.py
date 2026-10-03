import json
from src.risk.audit import serialize_audit_log
from src.risk.score import RiskScoreResult, MissingDataPolicy

def test_audit_serialization():
    result = RiskScoreResult(
        score=0.75,
        formula_version="heuristic-v0.1",
        weights={"w1": 0.5},
        factors={"f1": {"value": 1.0}},
        weighted_contributions={"f1": {"value": 1.0, "weight": 0.5, "contribution": 0.5}},
        missing_factors=[],
        missing_data_policy=MissingDataPolicy.STRICT,
        assumptions=["Test assumption"]
    )
    
    json_str = serialize_audit_log(result)
    parsed = json.loads(json_str)
    
    assert parsed["score"] == 0.75
    assert parsed["formula_version"] == "heuristic-v0.1"
    assert parsed["missing_data_policy"] == "STRICT"
    assert parsed["assumptions"] == ["Test assumption"]
