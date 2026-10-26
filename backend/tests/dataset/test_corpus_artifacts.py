import os
import json
import pytest
import torch
from src.dataset.models import CorpusManifest
from src.ml.converter import safe_load_pyg_data

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'artifacts')


@pytest.mark.skipif(not os.path.exists(os.path.join(ARTIFACTS_DIR, "manifest.json")), reason="Corpus artifacts not generated yet")
def test_corpus_manifest_validity():
    manifest_path = os.path.join(ARTIFACTS_DIR, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Pydantic validation
    manifest = CorpusManifest(**data)
    
    assert manifest.manifest_id == "corpus_v1"
    assert len(manifest.projects) == 8
    
    # Check that all artifacts exist
    for p in manifest.projects:
        artifact_path = os.path.join(ARTIFACTS_DIR, f"{p.project_id}.pt")
        assert os.path.exists(artifact_path)
        
        # Verify it loads as a PyG HeteroData safely
        pyg_data = safe_load_pyg_data(artifact_path)
        assert pyg_data is not None
        assert hasattr(pyg_data, "node_types")


@pytest.mark.skipif(not os.path.exists(os.path.join(ARTIFACTS_DIR, "report.json")), reason="Corpus report not generated yet")
def test_corpus_report_splits():
    report_path = os.path.join(ARTIFACTS_DIR, "report.json")
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    splits = report["splits"]
    assert len(splits["train"]) == 3
    assert len(splits["validation"]) == 3
    assert len(splits["test"]) == 2
