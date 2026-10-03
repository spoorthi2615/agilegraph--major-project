import re
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

JAVA_IMPORT_PATTERN = re.compile(r'import\s+(java\.security\.[a-zA-Z0-9_.*]+|javax\.crypto\.[a-zA-Z0-9_.*]+|org\.bouncycastle\.[a-zA-Z0-9_.*]+);')
# Broaden pattern to capture algorithms in strings, even if assigned to variables
JAVA_ALGO_PATTERN = re.compile(r'(Cipher|MessageDigest|KeyPairGenerator|KeyGenerator|Signature)\.getInstance\s*\(\s*([^)]+)\s*\)')
JAVA_KEY_SIZE_PATTERN = re.compile(r'\.initialize\s*\(\s*(\d+)\s*\)')

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
        usage_match = JAVA_ALGO_PATTERN.search(line)
        if usage_match:
            api = usage_match.group(1)
            algorithm_raw = usage_match.group(2).strip()
            
            # Extract string literal if it's there
            algorithm = algorithm_raw.strip('"\'')
            operation = "encryption" if "Cipher" in api else "hashing" if "MessageDigest" in api else "key_generation" if "Key" in api else "signature"
            
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                api=f"{api}.getInstance()",
                algorithm=algorithm,
                operation=operation,
                evidence=line.strip(),
                confidence=0.9,
                extra={}
            ))
            
        # Check key size
        key_size_match = JAVA_KEY_SIZE_PATTERN.search(line)
        if key_size_match:
            key_size = key_size_match.group(1)
            # Find the last key generation finding within the last 5 lines
            for f in reversed(findings):
                if f.asset_type == AssetType.CRYPTO_USAGE and f.operation == "key_generation":
                    if line_num - f.line <= 5:
                        if not f.extra:
                            f.extra = {}
                        if "key_size" not in f.extra:
                            f.extra["key_size"] = int(key_size)
                            f.evidence = f"{f.evidence} ... Key size {key_size}"
                            break
            
    return findings
