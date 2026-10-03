from src.scanners.dependencies.models import DependencyRecord
from src.scanners.common.enums import Language

def test_dependency_record_model():
    record = DependencyRecord(
        repository="repo",
        manifest_file="pom.xml",
        language=Language.JAVA,
        package_name="test-lib",
        ecosystem="maven",
        evidence="evidence",
        confidence=1.0
    )
    assert record.cve_ids is None
    assert record.crypto_relevance is None
    assert record.centrality is None
