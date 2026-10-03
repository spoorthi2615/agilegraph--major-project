from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.scanners.common.enums import Language

class DependencyRecord(BaseModel):
    repository: str
    manifest_file: str
    language: Language
    package_name: str
    version: Optional[str] = None
    ecosystem: str # pypi, maven, go
    direct: bool = True
    evidence: str
    confidence: float
    
    # Optional enrichment fields
    cve_ids: Optional[List[str]] = None
    deprecated: Optional[bool] = None
    unsupported: Optional[bool] = None
    crypto_relevance: Optional[str] = None
    centrality: Optional[float] = None
    
    extra: Dict[str, Any] = {}
