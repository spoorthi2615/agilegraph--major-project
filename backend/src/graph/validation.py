from src.graph.graph import AgileGraph

VALID_NODE_CATEGORIES = {"file", "crypto_usage", "certificate", "endpoint", "library", "sensitive_data"}
VALID_EDGE_RELATIONSHIPS = {"CONTAINS", "IMPORTS", "USES_CERT", "PROTECTS", "EXPOSES", "VULNERABLE_TO", "DEPENDS_ON", "CALLS"}

def validate_graph(graph: AgileGraph) -> list[str]:
    errors = []
    
    if len(graph.G.nodes) == 0:
        errors.append("Graph is empty")
        return errors

    # Check Nodes
    for node_id, data in graph.G.nodes(data=True):
        if "category" not in data:
            errors.append(f"Node {node_id} is missing 'category' property")
        elif data["category"] not in VALID_NODE_CATEGORIES:
            errors.append(f"Node {node_id} has invalid category: {data['category']}")
            
        if data.get("category") == "file" and "file" not in data:
            errors.append(f"File node {node_id} missing 'file' property")

    # Check Edges
    for u, v, key, data in graph.G.edges(keys=True, data=True):
        if "relationship" not in data:
            errors.append(f"Edge {u}->{v} is missing 'relationship' property")
        elif data["relationship"] not in VALID_EDGE_RELATIONSHIPS:
            errors.append(f"Edge {u}->{v} has invalid relationship: {data['relationship']}")
            
        # Dangling relationships theoretically shouldn't exist in NetworkX, but we can verify nodes exist
        if u not in graph.G.nodes:
            errors.append(f"Edge source {u} does not exist as a node")
        if v not in graph.G.nodes:
            errors.append(f"Edge target {v} does not exist as a node")

    return errors
