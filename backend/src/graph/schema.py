from pydantic import BaseModel
from typing import Dict, Any, Optional

class GraphNode(BaseModel):
    id: str
    category: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relationship: str
    properties: Dict[str, Any] = {}
