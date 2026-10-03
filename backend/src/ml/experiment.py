from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import datetime

class LabelRegime(str, Enum):
    SYNTHETIC = "SYNTHETIC" # Only for software validation
    EXPERT = "EXPERT"       # Actual human validation target

class AblationRegime(str, Enum):
    WITH_BASE_RISK = "WITH_BASE_RISK"
    WITHOUT_BASE_RISK = "WITHOUT_BASE_RISK"

class ModelType(str, Enum):
    GATV2 = "GATV2"
    HEURISTIC_BASELINE = "HEURISTIC_BASELINE"
    RULE_BASELINE = "RULE_BASELINE"
    CBOMKIT = "CBOMKIT"

class ExperimentManifest(BaseModel):
    experiment_id: str
    dataset_version: str
    project_split: Dict[str, List[str]] # e.g. {"train": [...], "val": [...], "test": [...]}
    feature_configuration: str
    include_base_risk: bool
    label_source: LabelRegime
    model_configuration: ModelType
    seed: int
    optimizer: Optional[str] = None
    learning_rate: Optional[float] = None
    epochs: Optional[int] = None
    batch_strategy: Optional[str] = None
    software_version: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())

class BaselineOutput(BaseModel):
    scores: Dict[str, float] # node_id -> risk_score
    audit_trail: Dict[str, Any]

class RuleConfig(BaseModel):
    version: str
    rules: List[str]
