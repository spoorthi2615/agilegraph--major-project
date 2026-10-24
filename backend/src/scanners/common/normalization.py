from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType
from src.graph.schema import GraphNode

def normalize_to_node(record: FindingRecord) -> GraphNode:
    if record.asset_type == AssetType.FILE:
        node_id = f"{record.repository}:{record.file}"
    else:
        suffix = record.api or record.operation or record.asset_type.value
        if record.line:
            node_id = f"{record.repository}:{record.file}:{record.line}:{suffix}"
        else:
            node_id = f"{record.repository}:{record.file}:{record.asset_type.value}"
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
