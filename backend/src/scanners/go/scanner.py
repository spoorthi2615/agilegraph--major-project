import re
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

GO_IMPORT_PATTERN = re.compile(r'"(crypto/(md5|sha1|des|rsa|ecdsa|ed25519|aes|cipher|sha256|sha512|hmac|tls)|github\.com/dgrijalva/jwt-go|github\.com/golang-jwt/jwt)"')
GO_CRYPTO_USAGE_PATTERN = re.compile(r'(md5\.New|sha1\.New|des\.NewCipher|rsa\.GenerateKey|ecdsa\.GenerateKey|ed25519\.GenerateKey|aes\.NewCipher|sha256\.New|sha512\.New|hmac\.New|tls\.Config|ecdsa\.Verify)\s*\(')
GO_JWT_SIGNING_METHOD_PATTERN = re.compile(r'\b(jwt\.SigningMethod[A-Za-z0-9_]+)\b')
GO_RSA_KEY_SIZE_PATTERN = re.compile(r'rsa\.GenerateKey\([^,]+,\s*(\d+)\)')

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
            elif algorithm in ("md5", "sha1", "sha256", "sha512", "hmac"):
                operation = "hashing"
            else:
                operation = "encryption"
                
            extra = {}
            if algorithm == "rsa":
                key_size_match = GO_RSA_KEY_SIZE_PATTERN.search(line)
                if key_size_match:
                    extra["key_size"] = int(key_size_match.group(1))
                    
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
                confidence=0.9,
                extra=extra
            ))
            
        # Check jwt signing methods
        for jwt_match in GO_JWT_SIGNING_METHOD_PATTERN.finditer(line):
            api = jwt_match.group(1)
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.GO,
                api=api,
                algorithm=api.replace("jwt.SigningMethod", ""),
                operation="signature",
                evidence=line.strip(),
                confidence=0.9,
                extra={}
            ))
            
    return findings
