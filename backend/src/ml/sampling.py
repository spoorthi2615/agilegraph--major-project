import random
from typing import List, Dict, Any
from .expert_validation import AssetForReview

def sample_held_out_assets(
    all_assets: List[Dict[str, Any]], 
    training_project_splits: List[str], 
    seed: int, 
    n_samples: int = 150
) -> List[AssetForReview]:
    """
    Deterministically samples held-out assets for expert validation.
    Enforces isolation by ensuring sampled assets are NEVER from training projects.
    """
    random.seed(seed)
    
    # Filter out assets belonging to training projects
    eligible_assets = [
        a for a in all_assets 
        if a["project_id"] not in training_project_splits
    ]
    
    if len(eligible_assets) < n_samples:
        n_samples = len(eligible_assets)
        
    # Sample without replacement
    sampled_raw = random.sample(eligible_assets, n_samples)
    
    # Convert to schema
    return [
        AssetForReview(
            asset_id=raw["asset_id"],
            project_id=raw["project_id"],
            heuristic_score=raw.get("heuristic_score")
        )
        for raw in sampled_raw
    ]
