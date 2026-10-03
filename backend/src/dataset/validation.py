from src.dataset.models import CorpusManifest, ProjectStatus, DataOrigin

class DatasetValidationError(Exception):
    pass

def validate_manifest(manifest: CorpusManifest):
    # Check for duplicate project IDs
    project_ids = [p.project_id for p in manifest.projects]
    if len(project_ids) != len(set(project_ids)):
        raise DatasetValidationError("Duplicate project_id detected in manifest.")
        
    # Check for duplicate commits
    commits = [p.commit_sha for p in manifest.projects if p.commit_sha]
    if len(commits) != len(set(commits)):
        raise DatasetValidationError("Duplicate commit_sha detected across projects.")

    for project in manifest.projects:
        # Check READY_FOR_MODELING requirements
        if project.status == ProjectStatus.READY_FOR_MODELING:
            if not project.commit_sha:
                raise DatasetValidationError(f"Project {project.project_id} missing commit_sha for READY status.")
            if not project.checkout_timestamp:
                raise DatasetValidationError(f"Project {project.project_id} missing checkout_timestamp for READY status.")
            if not project.scanner_provenance:
                raise DatasetValidationError(f"Project {project.project_id} missing scanner_provenance for READY status.")
            if not project.graph_provenance:
                raise DatasetValidationError(f"Project {project.project_id} missing graph_provenance for READY status.")
                
        # Validate Synthetic safety
        if project.origin == DataOrigin.SYNTHETIC:
            if "SYNTHETIC_TEST_DATA" not in project.metadata.values() and "NOT REAL SECURITY ASSESSMENT" not in project.metadata.values():
                raise DatasetValidationError(f"Synthetic project {project.project_id} missing required synthetic metadata labels.")
