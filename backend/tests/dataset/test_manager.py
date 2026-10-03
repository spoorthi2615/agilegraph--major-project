import pytest
from src.dataset.manager import DatasetManager
from src.dataset.models import CorpusProject, Language, SizeTier, DataOrigin, ProjectStatus, ScannerProvenance, GraphProvenance
from datetime import datetime

def _create_ready_project(idx):
    return CorpusProject(
        project_id=f"proj-{idx}",
        repository_url=f"https://github.com/example/{idx}",
        commit_sha=f"sha-{idx}",
        language=Language.PYTHON,
        size_tier=SizeTier.SMALL,
        origin=DataOrigin.PUBLIC_OPEN_SOURCE,
        status=ProjectStatus.READY_FOR_MODELING,
        checkout_timestamp=datetime.utcnow(),
        scanner_provenance=ScannerProvenance(scanner_version="v1", dependency_scan_version="v1"),
        graph_provenance=GraphProvenance(graph_version="v1", risk_calculation_version="v1")
    )

def test_manager_add_and_get():
    manager = DatasetManager("v1")
    p = _create_ready_project(1)
    manager.add_project(p)
    assert manager.get_project("proj-1") is not None

def test_manager_update_status():
    manager = DatasetManager("v1")
    p = _create_ready_project(1)
    p.status = ProjectStatus.PLANNED
    manager.add_project(p)
    
    # Try updating to READY_FOR_MODELING without missing fields
    # It has the required fields, so it should succeed
    manager.update_status("proj-1", ProjectStatus.READY_FOR_MODELING)
    assert manager.get_project("proj-1").status == ProjectStatus.READY_FOR_MODELING

def test_create_dataset_artifact():
    manager = DatasetManager("v1")
    for i in range(5):
        manager.add_project(_create_ready_project(i))
        
    artifact = manager.create_dataset_artifact(seed=123, train_ratio=0.6)
    assert artifact.metadata.split_strategy == "Deterministic Project-Level Shuffled Split"
    assert len(artifact.metadata.train_project_ids) == 3
    assert len(artifact.metadata.test_project_ids) == 2
