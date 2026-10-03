from src.dataset.models import CorpusProject, Language, SizeTier, DataOrigin, ProjectStatus
from datetime import datetime

def test_corpus_project_defaults():
    project = CorpusProject(
        project_id="test-1",
        repository_url="https://github.com/example/test",
        commit_sha="abcdef",
        language=Language.PYTHON,
        size_tier=SizeTier.SMALL,
        origin=DataOrigin.PUBLIC_OPEN_SOURCE
    )
    assert project.status == ProjectStatus.PLANNED
    assert project.scanner_provenance is None
    assert project.graph_provenance is None
