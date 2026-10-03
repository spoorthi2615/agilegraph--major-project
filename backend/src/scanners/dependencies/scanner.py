from typing import List
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.dependencies.python import parse_requirements_txt, parse_pyproject_toml
from src.scanners.dependencies.java import parse_pom_xml
from src.scanners.dependencies.go import parse_go_mod
from src.scanners.dependencies.cve import enrich_cves

def scan_manifest(repository: str, filepath: str, content: str) -> List[DependencyRecord]:
    if filepath.endswith("requirements.txt"):
        records = parse_requirements_txt(repository, filepath, content)
    elif filepath.endswith("pyproject.toml"):
        records = parse_pyproject_toml(repository, filepath, content)
    elif filepath.endswith("pom.xml"):
        records = parse_pom_xml(repository, filepath, content)
    elif filepath.endswith("go.mod"):
        records = parse_go_mod(repository, filepath, content)
    else:
        return []
        
    # Optional enrichment step interface
    for r in records:
        cve_data = enrich_cves(r.package_name, r.ecosystem, r.version or "")
        if cve_data.get("status") == "success":
            r.cve_ids = cve_data.get("cves", [])
            
    return records
