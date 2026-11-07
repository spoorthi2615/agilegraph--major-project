from __future__ import annotations
from typing import List, TYPE_CHECKING
from src.graph.schema import LEGAL_EDGE_TYPES, NodeCategory, EdgeRelationship

if TYPE_CHECKING:
    from src.graph.graph import AgileGraph

VALID_NODE_CATEGORIES = {c.value for c in NodeCategory}
VALID_EDGE_RELATIONSHIPS = {r.value for r in EdgeRelationship}


def validate_graph(graph: AgileGraph) -> list[str]:
    """
    Validates the structural integrity and schema legality of an AgileGraph instance.
    Checks:
      1. Non-empty graph.
      2. Valid node categories and mandatory attributes.
      3. No dangling edges (source and target nodes must exist).
      4. Schema legality: each edge triplet (source_cat, relationship, target_cat)
         must be in LEGAL_EDGE_TYPES per Synopsis 5.3.
    """
    errors = []
    g = graph.G if hasattr(graph, "G") else graph
    
    if len(g.nodes) == 0:
        errors.append("Graph is empty")
        return errors

    # Check Nodes
    for node_id, data in g.nodes(data=True):
        if "category" not in data:
            errors.append(f"Node {node_id} is missing 'category' property")
        elif data["category"] not in VALID_NODE_CATEGORIES:
            errors.append(f"Node {node_id} has invalid category: {data['category']}")
            
        if data.get("category") == "file" and "file" not in data:
            errors.append(f"File node {node_id} missing 'file' property")

    # Check Edges
    edge_iter = g.edges(keys=True, data=True) if getattr(g, "is_multigraph", lambda: False)() else g.edges(data=True)
    for edge in edge_iter:
        if len(edge) == 4:
            u, v, key, data = edge
        else:
            u, v, data = edge

        if "relationship" not in data:
            errors.append(f"Edge {u}->{v} is missing 'relationship' property")
            continue
            
        rel = data["relationship"]
        if rel not in VALID_EDGE_RELATIONSHIPS:
            errors.append(f"Edge {u}->{v} has invalid relationship: {rel}")
            continue
            
        # Dangling relationships check
        if u not in g.nodes:
            errors.append(f"Edge source {u} does not exist as a node (dangling edge)")
        if v not in g.nodes:
            errors.append(f"Edge target {v} does not exist as a node (dangling edge)")

        # Schema legality check: (source_category, relationship, target_category)
        if u in g.nodes and v in g.nodes:
            u_cat = g.nodes[u].get("category")
            v_cat = g.nodes[v].get("category")
            triplet = (u_cat, rel, v_cat)
            if triplet not in LEGAL_EDGE_TYPES:
                errors.append(
                    f"Schema violation: edge ({u_cat}, {rel}, {v_cat}) between '{u}' and '{v}' is not schema-legal."
                )

    return errors
