import re
from typing import List
from src.scanners.common.enums import Language
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.dependencies.normalization import classify_crypto_relevance

def parse_requirements_txt(repository: str, filepath: str, content: str) -> List[DependencyRecord]:
    records = []
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # very basic parse
        match = re.match(r'^([a-zA-Z0-9_\-]+)(.*)$', line)
        if match:
            pkg = match.group(1)
            version = match.group(2).strip() or None
            
            records.append(DependencyRecord(
                repository=repository,
                manifest_file=filepath,
                language=Language.PYTHON,
                package_name=pkg,
                version=version,
                ecosystem="pypi",
                direct=True,
                evidence=line,
                confidence=0.9,
                crypto_relevance=classify_crypto_relevance(pkg, "pypi")
            ))
    return records

def parse_pyproject_toml(repository: str, filepath: str, content: str) -> List[DependencyRecord]:
    # Simplified parsing for dependencies section
    records = []
    in_dependencies = False
    
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_dependencies = ("dependencies" in line.lower())
            continue
            
        if in_dependencies and line and not line.startswith("#"):
            # e.g., cryptography = "^3.4.7" or "cryptography>=3.0"
            parts = line.split("=")
            if len(parts) >= 1:
                # might be standard PEP 621 list or poetry dict
                pkg_raw = parts[0].strip().strip('"').strip("'")
                
                # PEP 621 list format: "cryptography>=3.0"
                match = re.match(r'^([a-zA-Z0-9_\-]+)(.*)$', pkg_raw)
                if match:
                    pkg = match.group(1)
                    version = match.group(2).strip() or (parts[1].strip() if len(parts) > 1 else None)
                    
                    records.append(DependencyRecord(
                        repository=repository,
                        manifest_file=filepath,
                        language=Language.PYTHON,
                        package_name=pkg,
                        version=version,
                        ecosystem="pypi",
                        direct=True,
                        evidence=line,
                        confidence=0.8,
                        crypto_relevance=classify_crypto_relevance(pkg, "pypi")
                    ))
    return records
