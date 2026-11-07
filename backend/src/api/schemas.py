from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class ScanRequest(BaseModel):
    repository_path: str
    project_id: str
    engine_version: Optional[str] = "v1"

class ScanResponse(BaseModel):
    project_id: str
    status: str
    message: str
    asset_count: Optional[int] = None
    scored_assets: Optional[int] = None
    unrated_assets: Optional[int] = None
    skipped_files: Optional[int] = None
    engine_version: Optional[str] = "v1"
    available_engine_versions: Optional[List[str]] = ["v1", "v2"]

class FactorContribution(BaseModel):
    value: float
    weight: float
    contribution: float

class RiskScore(BaseModel):
    asset_id: str
    score: Optional[float] = None
    scale: str = "0.0-1.0"
    formula_version: Optional[str] = None
    engine_version: Optional[str] = "v1"
    heuristic_label: Optional[Union[str, Dict[str, Any]]] = None
    v1_score: Optional[float] = None
    v1_label: Optional[Union[str, Dict[str, Any]]] = None
    v2_score: Optional[float] = None
    v2_label: Optional[Union[str, Dict[str, Any]]] = None
    comparison: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, float]] = None
    factors: Optional[Dict[str, Any]] = None
    weighted_contributions: Optional[Dict[str, FactorContribution]] = None
    missing_factors: Optional[List[str]] = None
    missing_data_policy: Optional[str] = None
    assumptions: Optional[List[str]] = None

class RiskResponse(BaseModel):
    project_id: str
    assets: List[RiskScore]
    active_engine_version: Optional[str] = "v1"
    available_engine_versions: Optional[List[str]] = ["v1", "v2"]
    ml_status: str = "ARCHITECTURAL_PROTOTYPE"

class GraphResponse(BaseModel):
    project_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class FeatureAttribution(BaseModel):
    feature_name: str
    importance: float
    normalized_importance: float

class InfluentialEdge(BaseModel):
    edge_type: str
    source_type: str
    source_idx: int
    relation: str
    target_type: str
    target_idx: int
    importance: float
    direct_incident: bool

class GNNExplanationResponse(BaseModel):
    asset_id: str
    project_id: str
    target_node_idx: Optional[int] = None
    heuristic_decomposition: Dict[str, Any]
    gnn_feature_attributions: List[FeatureAttribution]
    top_influential_edges: List[InfluentialEdge]
    ml_status: str = "ARCHITECTURAL_PROTOTYPE"
    caveat: str

