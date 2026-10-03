from typing import List, Optional
from src.dataset.models import CorpusManifest, CorpusProject, DatasetArtifact, DatasetMetadata, ProjectStatus
from src.dataset.validation import validate_manifest, DatasetValidationError
from src.dataset.splits import create_deterministic_split
import uuid

class DatasetManager:
    def __init__(self, dataset_generation_version: str):
        self.dataset_generation_version = dataset_generation_version
        self.manifest = CorpusManifest(
            manifest_id=str(uuid.uuid4()),
            dataset_generation_version=self.dataset_generation_version,
            projects=[]
        )
        
    def add_project(self, project: CorpusProject):
        self.manifest.projects.append(project)
        try:
            validate_manifest(self.manifest)
        except DatasetValidationError:
            # Rollback
            self.manifest.projects.pop()
            raise

    def get_project(self, project_id: str) -> Optional[CorpusProject]:
        for p in self.manifest.projects:
            if p.project_id == project_id:
                return p
        return None

    def update_status(self, project_id: str, new_status: ProjectStatus):
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")
            
        old_status = project.status
        project.status = new_status
        try:
            validate_manifest(self.manifest)
        except DatasetValidationError:
            project.status = old_status
            raise

    def create_dataset_artifact(self, seed: int = 42, train_ratio: float = 0.8) -> DatasetArtifact:
        """
        Creates a reproducible dataset artifact with a deterministic split.
        Only projects with status READY_FOR_MODELING will be included.
        """
        validate_manifest(self.manifest)
        
        train_ids, test_ids = create_deterministic_split(self.manifest, seed, train_ratio)
        
        if not train_ids and not test_ids:
            raise ValueError("No projects are READY_FOR_MODELING.")
            
        metadata = DatasetMetadata(
            seed=seed,
            split_strategy="Deterministic Project-Level Shuffled Split",
            train_project_ids=train_ids,
            test_project_ids=test_ids
        )
        
        return DatasetArtifact(
            artifact_id=str(uuid.uuid4()),
            manifest_id=self.manifest.manifest_id,
            metadata=metadata
        )
