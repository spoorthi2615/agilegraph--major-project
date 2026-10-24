import random
import networkx as nx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SampledAsset(BaseModel):
    asset_id: str
    project_id: str
    heuristic_score: Optional[float] = None

# Backward-compatible alias
AssetForReview = SampledAsset

def sample_held_out_assets(
    all_assets: List[Dict[str, Any]], 
    training_project_splits: List[str], 
    seed: int, 
    n_samples: int = 150
) -> List[SampledAsset]:
    """
    Deterministically samples held-out assets strictly partitioned by repository.
    Enforces repository-level isolation: sampled assets are NEVER from training projects.
    """
    rng = random.Random(seed)
    
    # Filter out assets belonging to training projects
    eligible_assets = [
        a for a in all_assets 
        if a["project_id"] not in training_project_splits
    ]
    
    if len(eligible_assets) < n_samples:
        n_samples = len(eligible_assets)
        
    sampled_raw = rng.sample(eligible_assets, n_samples)
    
    return [
        SampledAsset(
            asset_id=raw["asset_id"],
            project_id=raw["project_id"],
            heuristic_score=raw.get("heuristic_score")
        )
        for raw in sampled_raw
    ]


def partition_assets_by_repository(
    graph: nx.Graph,
    train_projects: List[str],
    test_projects: List[str]
) -> Dict[str, List[str]]:
    """
    Partitions graph nodes by repository and verifies zero cross-partition edges.
    Guarantees strict inductive evaluation boundaries.
    """
    train_set = set(train_projects)
    test_set = set(test_projects)
    
    # Overlap assertion
    overlap = train_set.intersection(test_set)
    if overlap:
        raise ValueError(f"Repository leakage detected: projects in both train and test: {overlap}")
        
    train_nodes = []
    test_nodes = []
    
    for node_id, data in graph.nodes(data=True):
        proj = data.get("project_id") or node_id.split(":")[0] if ":" in str(node_id) else None
        if proj in train_set:
            train_nodes.append(node_id)
        elif proj in test_set:
            test_nodes.append(node_id)
            
    # Edge boundary verification: zero edges between train_nodes and test_nodes
    train_node_set = set(train_nodes)
    test_node_set = set(test_nodes)
    
    for u, v in graph.edges():
        if (u in train_node_set and v in test_node_set) or (u in test_node_set and v in train_node_set):
            raise ValueError(f"Cross-partition edge detected between {u} and {v}! Zero edges allowed across repository partitions.")
            
    return {
        "train": train_nodes,
        "test": test_nodes
    }
