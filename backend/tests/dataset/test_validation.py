import pytest
from src.dataset.models import CorpusManifest, CorpusProject, Language, SizeTier, DataOrigin, ProjectStatus, ScannerProvenance, GraphProvenance
from src.dataset.validation import validate_manifest, DatasetValidationError
from datetime import datetime

def _create_project(id_val, sha_val):
    return CorpusProject(
        project_id=id_val,
        repository_url=f"https://github.com/ex/{id_val}",
        commit_sha=sha_val,
        language=Language.PYTHON,
        size_tier=SizeTier.SMALL,
        origin=DataOrigin.PUBLIC_OPEN_SOURCE
    )

def test_duplicate_project_id():
    manifest = CorpusManifest(
        manifest_id="m", dataset_generation_version="v1",
        projects=[_create_project("p1", "sha1"), _create_project("p1", "sha2")]
    )
    with pytest.raises(DatasetValidationError, match="Duplicate project_id"):
        validate_manifest(manifest)

def test_duplicate_commit_sha():
    manifest = CorpusManifest(
        manifest_id="m", dataset_generation_version="v1",
        projects=[_create_project("p1", "sha1"), _create_project("p2", "sha1")]
    )
    with pytest.raises(DatasetValidationError, match="Duplicate commit_sha"):
        validate_manifest(manifest)

def test_ready_requirements():
    p = _create_project("p1", "sha1")
    p.status = ProjectStatus.READY_FOR_MODELING
    manifest = CorpusManifest(manifest_id="m", dataset_generation_version="v1", projects=[p])
    
    with pytest.raises(DatasetValidationError, match="missing checkout_timestamp"):
        validate_manifest(manifest)
        
    p.checkout_timestamp = datetime.utcnow()
    p.scanner_provenance = ScannerProvenance(scanner_version="v1", dependency_scan_version="v1")
    p.graph_provenance = GraphProvenance(graph_version="v1", risk_calculation_version="v1")
    
    # Now it should pass
    validate_manifest(manifest)

def test_synthetic_metadata():
    p = _create_project("p1", "sha1")
    p.origin = DataOrigin.SYNTHETIC
    manifest = CorpusManifest(manifest_id="m", dataset_generation_version="v1", projects=[p])
    
    with pytest.raises(DatasetValidationError, match="missing required synthetic metadata"):
        validate_manifest(manifest)
        
    p.metadata = {"label": "SYNTHETIC_TEST_DATA"}
    validate_manifest(manifest)
