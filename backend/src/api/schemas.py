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

class RiskScore(BaseModel):
    asset_id: str
    score: float
    data_sensitivity: Optional[float] = None
    asset_criticality: Optional[float] = None
    internet_exposure: Optional[float] = None
    crypto_weakness: Optional[float] = None
    cve_risk: Optional[float] = None
    library_centrality: Optional[float] = None
    migration_difficulty: Optional[float] = None

class RiskResponse(BaseModel):
    project_id: str
    assets: List[RiskScore]
    ml_status: str = "BLOCKED"
    expert_validation_status: str = "BLOCKED"

class GraphResponse(BaseModel):
    project_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
