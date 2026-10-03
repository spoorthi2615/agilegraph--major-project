from pydantic import BaseModel
from typing import List, Optional

class BaseNode(BaseModel):
    id: str
    risk_score: Optional[float] = None

class FileNode(BaseNode):
    path: str
    language: str

class CryptoUsageNode(BaseNode):
    algorithm: str
    strength: Optional[int] = None

class CertificateNode(BaseNode):
    issuer: str
    expiry: str
    is_expired: bool = False

class EndpointNode(BaseNode):
    url: str
    tls_version: str

class LibraryNode(BaseNode):
    name: str
    version: str
    has_cves: bool = False

class SensitiveDataNode(BaseNode):
    data_type: str
    sensitivity_level: str
