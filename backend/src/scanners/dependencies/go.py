import re
from typing import List
from src.scanners.common.enums import Language
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.dependencies.normalization import classify_crypto_relevance

def parse_go_mod(repository: str, filepath: str, content: str) -> List[DependencyRecord]:
    records = []
    lines = content.splitlines()
    in_require_block = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("//"):
            continue
            
        if line == "require (":
            in_require_block = True
            continue
        if line == ")" and in_require_block:
            in_require_block = False
            continue
            
        if line.startswith("require "):
            # single require
            parts = line.split()
            if len(parts) >= 3:
                pkg = parts[1]
                version = parts[2]
                records.append(_build_go_record(repository, filepath, pkg, version, line))
        elif in_require_block:
            parts = line.split()
            if len(parts) >= 2:
                pkg = parts[0]
                version = parts[1]
                indirect = "// indirect" in line
                records.append(_build_go_record(repository, filepath, pkg, version, line, not indirect))
                
    return records

def _build_go_record(repository: str, filepath: str, pkg: str, version: str, line: str, direct: bool = True) -> DependencyRecord:
    return DependencyRecord(
        repository=repository,
        manifest_file=filepath,
        language=Language.GO,
        package_name=pkg,
        version=version,
        ecosystem="go",
        direct=direct,
        evidence=line,
        confidence=0.9,
        crypto_relevance=classify_crypto_relevance(pkg, "go")
    )
