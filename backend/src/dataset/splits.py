from typing import List, Tuple, Set
from src.dataset.models import CorpusManifest, CorpusProject, DataOrigin
import random

def create_deterministic_split(
    manifest: CorpusManifest, 
    seed: int = 42, 
    train_ratio: float = 0.8
) -> Tuple[List[str], List[str]]:
    """
    Creates a deterministic project-level split to prevent repository leakage.
    Returns (train_project_ids, test_project_ids).
    Does NOT mix synthetic and real datasets unless explicitly isolated.
    For this phase, it just randomly shuffles and splits project IDs.
    """
    # Filter to only projects ready for modeling
    ready_projects = [
        p for p in manifest.projects 
        if p.status == "READY_FOR_MODELING"
    ]
    
    # We should not allow mixing synthetic and non-synthetic in a real model split
    origins = {p.origin for p in ready_projects}
    if DataOrigin.SYNTHETIC in origins and len(origins) > 1:
        raise ValueError("Cannot mix SYNTHETIC and real data in the same training split.")
        
    project_ids = sorted([p.project_id for p in ready_projects])
    
    # Deterministic random split
    rng = random.Random(seed)
    rng.shuffle(project_ids)
    
    split_idx = int(len(project_ids) * train_ratio)
    train_ids = project_ids[:split_idx]
    test_ids = project_ids[split_idx:]
    
    # Safety assertion to prevent overlap
    assert len(set(train_ids).intersection(set(test_ids))) == 0, "Leakage detected: train/test project overlap."
    
    return train_ids, test_ids
