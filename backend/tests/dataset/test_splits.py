import pytest
from src.dataset.models import CorpusManifest, CorpusProject, Language, SizeTier, DataOrigin, ProjectStatus
from src.dataset.splits import create_deterministic_split

def _create_project(idx, origin=DataOrigin.PUBLIC_OPEN_SOURCE):
    return CorpusProject(
        project_id=f"proj-{idx}",
        repository_url=f"https://github.com/example/{idx}",
        commit_sha=f"sha-{idx}",
        language=Language.PYTHON,
        size_tier=SizeTier.SMALL,
        origin=origin,
        status=ProjectStatus.READY_FOR_MODELING
    )

def test_deterministic_split():
    manifest = CorpusManifest(
        manifest_id="m-1", 
        dataset_generation_version="v1",
        projects=[_create_project(i) for i in range(10)]
    )
    train_ids, test_ids = create_deterministic_split(manifest, seed=42, train_ratio=0.8)
    
    assert len(train_ids) == 8
    assert len(test_ids) == 2
    assert len(set(train_ids).intersection(set(test_ids))) == 0
    
    # Check determinism
    train_ids2, test_ids2 = create_deterministic_split(manifest, seed=42, train_ratio=0.8)
    assert train_ids == train_ids2
    assert test_ids == test_ids2

def test_split_prevents_mixing():
    manifest = CorpusManifest(
        manifest_id="m-1", 
        dataset_generation_version="v1",
        projects=[
            _create_project(1, DataOrigin.PUBLIC_OPEN_SOURCE),
            _create_project(2, DataOrigin.SYNTHETIC)
        ]
    )
    with pytest.raises(ValueError, match="Cannot mix SYNTHETIC and real data"):
        create_deterministic_split(manifest)
