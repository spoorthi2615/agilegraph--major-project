from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ScanRequest(BaseModel):
    repository_path: str
    project_id: str

class ScanResponse(BaseModel):
    project_id: str
    status: str
    message: str
    asset_count: Optional[int] = None

class FactorContribution(BaseModel):
    value: float
    weight: float
    contribution: float

class RiskScore(BaseModel):
    asset_id: str
    score: float
    scale: str = "0.0-1.0"
    formula_version: Optional[str] = None
    weights: Optional[Dict[str, float]] = None
    factors: Optional[Dict[str, Any]] = None
    weighted_contributions: Optional[Dict[str, FactorContribution]] = None
    missing_factors: Optional[List[str]] = None
    missing_data_policy: Optional[str] = None
    assumptions: Optional[List[str]] = None

class RiskResponse(BaseModel):
    project_id: str
    assets: List[RiskScore]
    ml_status: str = "BLOCKED"
    expert_validation_status: str = "BLOCKED"

class GraphResponse(BaseModel):
    project_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
