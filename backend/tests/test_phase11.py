import os
import json
import pytest
import torch
from src.dataset.models import CorpusManifest

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'artifacts')

@pytest.mark.skipif(not os.path.exists(os.path.join(ARTIFACTS_DIR, "manifest.json")), reason="Phase 11 corpus not generated yet")
def test_phase11_manifest_validity():
    manifest_path = os.path.join(ARTIFACTS_DIR, "manifest.json")
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    # Pydantic validation
    manifest = CorpusManifest(**data)
    
    assert manifest.manifest_id == "phase11_corpus"
    assert len(manifest.projects) == 8
    
    # Check that all artifacts exist
    for p in manifest.projects:
        artifact_path = os.path.join(ARTIFACTS_DIR, f"{p.project_id}.pt")
        assert os.path.exists(artifact_path)
        
        # Verify it loads as a PyG HeteroData
        pyg_data = torch.load(artifact_path, weights_only=False)
        assert pyg_data is not None
        assert hasattr(pyg_data, "node_types")

@pytest.mark.skipif(not os.path.exists(os.path.join(ARTIFACTS_DIR, "report.json")), reason="Phase 11 corpus not generated yet")
def test_phase11_report_splits():
    report_path = os.path.join(ARTIFACTS_DIR, "report.json")
    with open(report_path, "r") as f:
        report = json.load(f)
        
    splits = report["splits"]
    assert len(splits["train"]) == 3
    assert len(splits["validation"]) == 3
    assert len(splits["test"]) == 2
