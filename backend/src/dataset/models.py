from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime

class DataOrigin(str, Enum):
    PUBLIC_OPEN_SOURCE = "PUBLIC_OPEN_SOURCE"
    SYNTHETIC = "SYNTHETIC"
    USER_AUTHORIZED = "USER_AUTHORIZED"
    UNKNOWN = "UNKNOWN"

class ProjectStatus(str, Enum):
    PLANNED = "PLANNED"
    ACQUIRED = "ACQUIRED"
    SCANNED = "SCANNED"
    GRAPH_BUILT = "GRAPH_BUILT"
    RISK_SCORED = "RISK_SCORED"
    READY_FOR_MODELING = "READY_FOR_MODELING"

class SizeTier(str, Enum):
    SMALL = "SMALL"
    LARGE = "LARGE"

class Language(str, Enum):
    PYTHON = "PYTHON"
    JAVA = "JAVA"
    GO = "GO"

class ScannerProvenance(BaseModel):
    scanner_version: str
    dependency_scan_version: str

class GraphProvenance(BaseModel):
    graph_version: str
    risk_calculation_version: str

class CorpusProject(BaseModel):
    project_id: str
    repository_url: str
    commit_sha: str
    language: Language
    size_tier: SizeTier
    origin: DataOrigin
    status: ProjectStatus = ProjectStatus.PLANNED
    checkout_timestamp: Optional[datetime] = None
    
    # Traceability
    scanner_provenance: Optional[ScannerProvenance] = None
    graph_provenance: Optional[GraphProvenance] = None
    
    metadata: Dict[str, str] = Field(default_factory=dict)

class CorpusManifest(BaseModel):
    manifest_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    dataset_generation_version: str
    projects: List[CorpusProject]

class DatasetMetadata(BaseModel):
    seed: int
    split_strategy: str
    train_project_ids: List[str]
    test_project_ids: List[str]

class DatasetArtifact(BaseModel):
    artifact_id: str
    manifest_id: str
    metadata: DatasetMetadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
