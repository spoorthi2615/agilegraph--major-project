import pytest
from src.ml.sampling import sample_held_out_assets

def test_held_out_sampling_isolation():
    all_assets = [
        {"asset_id": "f1", "project_id": "train_proj"},
        {"asset_id": "f2", "project_id": "val_proj"},
        {"asset_id": "f3", "project_id": "test_proj"}
    ]
    
    sampled = sample_held_out_assets(all_assets, ["train_proj"], seed=42, n_samples=10)
    
    assert len(sampled) == 2
    assert "f1" not in [s.asset_id for s in sampled]
    
def test_held_out_sampling_determinism():
    all_assets = [{"asset_id": f"f{i}", "project_id": "val_proj"} for i in range(100)]
    
    s1 = sample_held_out_assets(all_assets, [], seed=42, n_samples=10)
    s2 = sample_held_out_assets(all_assets, [], seed=42, n_samples=10)
    
    assert [s.asset_id for s in s1] == [s.asset_id for s in s2]
