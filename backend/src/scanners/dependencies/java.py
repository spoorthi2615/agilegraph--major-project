import xml.etree.ElementTree as ET
from typing import List
from src.scanners.common.enums import Language
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.dependencies.normalization import classify_crypto_relevance

def parse_pom_xml(repository: str, filepath: str, content: str) -> List[DependencyRecord]:
    records = []
    try:
        root = ET.fromstring(content)
        # Handle namespaces simply by ignoring them in tags
        for dep in root.iter():
            if dep.tag.endswith('dependency'):
                group_id = ""
                artifact_id = ""
                version = None
                
                for child in dep:
                    if child.tag.endswith('groupId'): group_id = child.text
                    elif child.tag.endswith('artifactId'): artifact_id = child.text
                    elif child.tag.endswith('version'): version = child.text
                
                if group_id and artifact_id:
                    pkg_name = f"{group_id}:{artifact_id}"
                    records.append(DependencyRecord(
                        repository=repository,
                        manifest_file=filepath,
                        language=Language.JAVA,
                        package_name=pkg_name,
                        version=version,
                        ecosystem="maven",
                        direct=True,
                        evidence=f"POM dependency {pkg_name}",
                        confidence=0.9,
                        crypto_relevance=classify_crypto_relevance(pkg_name, "maven")
                    ))
    except ET.ParseError:
        pass
    return records
