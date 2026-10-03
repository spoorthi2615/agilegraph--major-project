from src.scanners.common.models import FindingRecord
from src.graph.schema import GraphNode

def normalize_to_node(record: FindingRecord) -> GraphNode:
    node_id = f"{record.repository}:{record.file}:{record.line}:{record.api}" if record.line else f"{record.repository}:{record.file}"
    properties = {
        "repository": record.repository,
        "file": record.file,
        "line": record.line,
        "language": record.language.value if record.language else None,
        "library": record.library,
        "api": record.api,
        "algorithm": record.algorithm,
        "operation": record.operation,
        "evidence": record.evidence,
        "confidence": record.confidence,
        **record.extra
    }
    # Clean up None values
    properties = {k: v for k, v in properties.items() if v is not None}
    
    return GraphNode(
        id=node_id,
        category=record.asset_type.value,
        properties=properties
    )
