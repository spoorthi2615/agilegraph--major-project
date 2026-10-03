from src.scanners.dependencies.scanner import scan_manifest
from src.scanners.dependencies.models import DependencyRecord
import pytest

def test_parse_requirements_txt():
    content = "cryptography==3.4.7\nrequests>=2.0\n# comment\n"
    records = scan_manifest("repo", "requirements.txt", content)
    assert len(records) == 2
    assert records[0].package_name == "cryptography"
    assert records[0].version == "==3.4.7"
    assert records[0].crypto_relevance == "CRYPTOGRAPHIC"

def test_parse_pyproject_toml():
    content = "[tool.poetry.dependencies]\npython = \"^3.9\"\ncryptography = \"^3.4\"\n"
    records = scan_manifest("repo", "pyproject.toml", content)
    assert len(records) == 2
    crypto = [r for r in records if r.package_name == "cryptography"][0]
    assert crypto.version == "\"^3.4\""
