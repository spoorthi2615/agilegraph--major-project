from enum import Enum
from typing import Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field


class NodeCategory(str, Enum):
    FILE = "file"
    CRYPTO_USAGE = "crypto_usage"
    CERTIFICATE = "certificate"
    ENDPOINT = "endpoint"
    LIBRARY = "library"
    SENSITIVE_DATA = "sensitive_data"


class EdgeRelationship(str, Enum):
    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"
    EXPOSES = "EXPOSES"
    PROTECTS = "PROTECTS"
    USES_CERT = "USES_CERT"


# Authoritative legal (source_category, relationship, target_category) triplets per Synopsis 5.3:
# - endpoint -> exposes -> crypto usage
# - crypto usage -> protects -> sensitive data
# - crypto usage / endpoint -> uses -> certificate
# - file -> calls -> endpoint
# - file -> contains -> crypto usage / certificate / sensitive data
# - file -> imports / depends_on -> library
LEGAL_EDGE_TYPES: Set[Tuple[str, str, str]] = {
    # File containment of cryptographic assets
    ("file", "CONTAINS", "crypto_usage"),
    ("file", "CONTAINS", "certificate"),
    ("file", "CONTAINS", "sensitive_data"),
    # File dependencies (source code imports and manifest dependencies)
    ("file", "IMPORTS", "library"),
    ("file", "DEPENDS_ON", "library"),
    # File calling endpoint
    ("file", "CALLS", "endpoint"),
    # Endpoint exposing cryptographic usage
    ("endpoint", "EXPOSES", "crypto_usage"),
    # Cryptographic protection of sensitive data
    ("crypto_usage", "PROTECTS", "sensitive_data"),
    # Cryptographic usage calling library
    ("crypto_usage", "CALLS", "library"),
    # Cryptographic usage or endpoint using a certificate
    ("crypto_usage", "USES_CERT", "certificate"),
    ("endpoint", "USES_CERT", "certificate"),
}


class GraphNode(BaseModel):
    id: str
    category: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)
