from src.risk.factors import FactorValue
from src.graph.graph import AgileGraph


def calculate_in_degree_centrality(graph: AgileGraph, node_id: str) -> FactorValue:
    """
    Direct in-degree centrality calculation for library nodes:
    normalized = in_degree / (total_nodes - 1).
    """
    if node_id not in graph.G.nodes:
        return FactorValue(value=None, source="Node not in graph", confidence=0.0)
        
    node_data = graph.G.nodes[node_id]
    if node_data.get("category") != "library":
        return FactorValue(value=None, source="Not applicable for non-library nodes", confidence=0.0)
        
    in_degree = graph.G.in_degree(node_id)
    total_nodes = len(graph.G.nodes)
    
    if total_nodes <= 1:
        return FactorValue(value=0.0, source="in-degree centrality", confidence=1.0)
        
    normalized = in_degree / (total_nodes - 1)
    
    return FactorValue(value=round(min(max(normalized, 0.0), 1.0), 4), source="in-degree centrality", confidence=1.0)


def calculate_library_centrality_for_file(
    graph: AgileGraph, 
    file_node_id: str, 
    connected_libraries: list = None
) -> FactorValue:
    """
    Computes a file-level aggregation of the in-degree centrality of libraries
    connected to the file (via IMPORTS or DEPENDS_ON).
    
    Aggregation method: Maximum in-degree centrality (peak dependency blast radius).
    Rationale: In post-quantum cryptographic migration, a module's structural exposure
    is driven by its most central shared dependency. Updating a widely-imported dependency
    carries high coordination friction and broad blast radius.
    
    Missing-data semantics:
    - If no library nodes exist in the graph, or the file has no connected libraries,
      returns value=None (source="no connected libraries", confidence=0.0).
      This preserves epistemic uncertainty for renormalization or conservative policy,
      preventing silent conversion to a misleading zero.
    """
    if file_node_id not in graph.G.nodes:
        return FactorValue(value=None, source="Node not in graph", confidence=0.0)

    total_nodes = len(graph.G.nodes)
    if total_nodes <= 1:
        return FactorValue(value=None, source="no connected libraries", confidence=0.0)

    # If connected libraries not provided, discover via graph out-edges
    if connected_libraries is None:
        connected_libraries = []
        for _, target, edge_data in graph.G.out_edges(file_node_id, data=True):
            rel = edge_data.get("relationship")
            t_data = graph.G.nodes.get(target, {})
            if t_data.get("category") == "library" or rel in ("IMPORTS", "DEPENDS_ON"):
                if t_data.get("category") == "library":
                    connected_libraries.append((target, t_data))

    if not connected_libraries:
        return FactorValue(value=None, source="no connected libraries", confidence=0.0)

    lib_centralities = []
    for item in connected_libraries:
        if isinstance(item, tuple):
            lib_id, lib_data = item
        elif isinstance(item, dict):
            lib_id = item.get("id")
            lib_data = item
            if not lib_id:
                for nid, ndata in graph.G.nodes(data=True):
                    if ndata == item or (ndata.get("category") == "library" and ndata.get("library") == item.get("library")):
                        lib_id = nid
                        break
        else:
            lib_id = str(item)
            lib_data = graph.G.nodes.get(lib_id, {})

        if lib_id and lib_id in graph.G.nodes:
            in_deg = graph.G.in_degree(lib_id)
            cent = in_deg / (total_nodes - 1)
            lib_name = lib_data.get("library") or lib_data.get("package_name") or str(lib_id).split(":")[-1]
            lib_centralities.append((cent, lib_name))

    if not lib_centralities:
        return FactorValue(value=None, source="no connected libraries", confidence=0.0)

    max_cent, max_lib_name = max(lib_centralities, key=lambda x: x[0])
    bounded_val = round(min(max(max_cent, 0.0), 1.0), 4)

    return FactorValue(
        value=bounded_val,
        source=f"max library in-degree centrality: {max_lib_name} ({bounded_val:.4f})",
        confidence=0.85
    )
