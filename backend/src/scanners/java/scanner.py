import re
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

JAVA_IMPORT_PATTERN = re.compile(r'import\s+(java\.security\.[a-zA-Z0-9_.*]+|javax\.crypto\.[a-zA-Z0-9_.*]+|org\.bouncycastle\.[a-zA-Z0-9_.*]+);')
JAVA_CRYPTO_USAGE_PATTERN = re.compile(r'(Cipher\.getInstance|MessageDigest\.getInstance|KeyPairGenerator\.getInstance|KeyGenerator\.getInstance|Signature\.getInstance)\s*\(\s*"([^"]+)"\s*\)')

def scan_java_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check imports
        import_match = JAVA_IMPORT_PATTERN.search(line)
        if import_match:
            pkg = import_match.group(1)
            findings.append(FindingRecord(
                asset_type=AssetType.LIBRARY,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                library=pkg,
                evidence=f"Imported {pkg}",
                confidence=1.0
            ))
            
        # Check usages
        usage_match = JAVA_CRYPTO_USAGE_PATTERN.search(line)
        if usage_match:
            api = usage_match.group(1)
            algorithm = usage_match.group(2)
            operation = "encryption" if "Cipher" in api else "hashing" if "MessageDigest" in api else "key_generation" if "Key" in api else "signature"
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                api=f"{api}()",
                algorithm=algorithm,
                operation=operation,
                evidence=line.strip(),
                confidence=0.9
            ))
            
    return findings
