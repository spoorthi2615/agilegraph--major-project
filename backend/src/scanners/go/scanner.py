import re
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

GO_IMPORT_PATTERN = re.compile(r'"(crypto/rsa|crypto/ecdsa|crypto/ed25519|crypto/aes|crypto/cipher|crypto/sha256|crypto/sha512|crypto/tls)"')
GO_CRYPTO_USAGE_PATTERN = re.compile(r'(rsa\.GenerateKey|ecdsa\.GenerateKey|ed25519\.GenerateKey|aes\.NewCipher|sha256\.New|sha512\.New|tls\.Config)\s*\(')

def scan_go_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check imports (basic check looking for string literal in import block or single import)
        import_match = GO_IMPORT_PATTERN.search(line)
        if import_match:
            pkg = import_match.group(1)
            findings.append(FindingRecord(
                asset_type=AssetType.LIBRARY,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.GO,
                library=pkg,
                evidence=f"Imported {pkg}",
                confidence=0.9
            ))
            
        # Check usages
        usage_match = GO_CRYPTO_USAGE_PATTERN.search(line)
        if usage_match:
            api = usage_match.group(1)
            algorithm = api.split('.')[0]
            if algorithm == "tls":
                operation = "tls_config"
            elif "GenerateKey" in api:
                operation = "key_generation"
            elif algorithm in ("sha256", "sha512"):
                operation = "hashing"
            else:
                operation = "encryption"
                
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.GO,
                api=f"{api}()",
                algorithm=algorithm,
                operation=operation,
                evidence=line.strip(),
                confidence=0.9
            ))
            
    return findings
