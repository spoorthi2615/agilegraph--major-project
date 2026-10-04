import torch
from torch_geometric.data import HeteroData
from src.graph.graph import AgileGraph
from src.ml.features import FeatureConfig, extract_node_features, extract_target_label

def convert_agilegraph_to_pyg(ag: AgileGraph, config: FeatureConfig) -> HeteroData:
    """
    Deterministically converts the NetworkX-based AgileGraph into a PyTorch Geometric HeteroData object.
    Preserves node types, edge types, feature provenance, and graph identity.
    """
    data = HeteroData()
    
    # Track node mapping for edges: node_id -> integer index per category
    node_maps = {}
    initialized_categories = set()
    
    # 1. Process Nodes
    # The 6 synopsis categories: file, cryptousage, certificate, endpoint, library, sensitivedata
    for n_id, data_dict in ag.G.nodes(data=True):
        category = data_dict.get("category", "unknown_node")
        
        if category not in node_maps:
            node_maps[category] = {}
            
        current_idx = len(node_maps[category])
        node_maps[category][n_id] = current_idx
        
        # We will build up tensors for this category
        if category not in initialized_categories:
            initialized_categories.add(category)
            data[category].x = []
            data[category].y = []
            data[category].node_ids = [] # Store original IDs
            data[category].label_sources = []
            
        # In some schemas, properties might be flattened or stored under 'properties'
        props = data_dict.get("properties", data_dict)
        x_feat = extract_node_features(props, config)
        y_label = extract_target_label(props)
        
        data[category].x.append(x_feat)
        data[category].y.append(y_label.class_idx if y_label.class_idx is not None else -1) # -1 means no label
        data[category].node_ids.append(n_id)
        data[category].label_sources.append(y_label.source.value)
        
    # Convert lists to tensors
    for category in node_maps.keys():
        if len(data[category].x) > 0:
            data[category].x = torch.stack(data[category].x)
            data[category].y = torch.tensor(data[category].y, dtype=torch.long)
            
    # 2. Process Edges
    edge_lists = {}
    for u, v, k, e_data in ag.G.edges(data=True, keys=True):
        u_cat = ag.G.nodes[u].get("category", "unknown_node")
        v_cat = ag.G.nodes[v].get("category", "unknown_node")
        edge_type = e_data.get("relationship", "unknown_edge")
        
        edge_triplet = (u_cat, edge_type, v_cat)
        if edge_triplet not in edge_lists:
            edge_lists[edge_triplet] = [[], []] # [source_indices, target_indices]
            
        u_idx = node_maps[u_cat][u]
        v_idx = node_maps[v_cat][v]
        
        edge_lists[edge_triplet][0].append(u_idx)
        edge_lists[edge_triplet][1].append(v_idx)
        
    for triplet, edge_index in edge_lists.items():
        data[triplet].edge_index = torch.tensor(edge_index, dtype=torch.long)
        
    # The GNN needs information to flow from neighbors (libraries, cryptousage) back to the file node
    import torch_geometric.transforms as T
    data = T.ToUndirected()(data)
        
    return data
