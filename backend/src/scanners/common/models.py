from pydantic import BaseModel
from typing import Optional, Dict, Any
from src.scanners.common.enums import AssetType, Language

class FindingRecord(BaseModel):
    asset_type: AssetType
    repository: str
    file: Optional[str] = None
    line: Optional[int] = None
    language: Optional[Language] = None
    library: Optional[str] = None
    api: Optional[str] = None
    algorithm: Optional[str] = None
    operation: Optional[str] = None
    evidence: str
    confidence: float
    extra: Dict[str, Any] = {}
