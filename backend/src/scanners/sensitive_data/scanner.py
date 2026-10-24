import re
from typing import List, Dict, Tuple
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

# Sensitive identifier keywords and their classification levels
SENSITIVE_CLASSIFICATIONS = {
    # CRITICAL: Root keys, raw passwords, private keys
    "private_key": "CRITICAL",
    "privkey": "CRITICAL",
    "signing_key": "CRITICAL",
    "master_key": "CRITICAL",
    "password": "CRITICAL",
    "passwd": "CRITICAL",
    "passphrase": "CRITICAL",
    "pin": "CRITICAL",

    # HIGH: Credentials, tokens, financial, PII
    "secret_key": "HIGH",
    "api_key": "HIGH",
    "api_secret": "HIGH",
    "auth_token": "HIGH",
    "jwt_secret": "HIGH",
    "access_token": "HIGH",
    "refresh_token": "HIGH",
    "bearer_token": "HIGH",
    "encryption_key": "HIGH",
    "credit_card": "HIGH",
    "card_number": "HIGH",
    "cvv": "HIGH",
    "ssn": "HIGH",
    "social_security": "HIGH",
    "bank_account": "HIGH",
    "iban": "HIGH",

    # MEDIUM: Sessions, client secrets, health ids
    "session_id": "MEDIUM",
    "session_token": "MEDIUM",
    "client_secret": "MEDIUM",
    "oauth_secret": "MEDIUM",
    "medical_record": "MEDIUM",
    "patient_id": "MEDIUM"
}

# Regex to detect sensitive variables/fields in code
# E.g. password = "...", private_key: str, String password;, Password string
SENSITIVE_VAR_PATTERN = re.compile(
    r'\b(?P<name>[a-zA-Z0-9_]*(?:' +
    '|'.join(re.escape(k) for k in sorted(SENSITIVE_CLASSIFICATIONS.keys(), key=len, reverse=True)) +
    r')[a-zA-Z0-9_]*)\b\s*(?:=|:=|:|\bstring\b|\bint\b|\bbyte\[\]\b|\bString\b)',
    re.IGNORECASE
)

# Variable declaration in Java: String password; or byte[] privateKey;
JAVA_SENSITIVE_FIELD_PATTERN = re.compile(
    r'\b(?:String|byte\[\]|char\[\]|SecretKey|PrivateKey)\s+(?P<name>[a-zA-Z0-9_]+)\b',
    re.IGNORECASE
)

# Variable declaration in Go: Password string or PrivateKey []byte
GO_SENSITIVE_FIELD_PATTERN = re.compile(
    r'\b(?P<name>[A-Z][a-zA-Z0-9_]*)\s+(?:string|\[\]byte|\*rsa\.PrivateKey|\*ecdsa\.PrivateKey)\b'
)


def classify_identifier(name: str) -> Tuple[str, str]:
    """Finds best matching keyword and assigns sensitivity classification."""
    name_lower = name.lower()
    for kw, level in sorted(SENSITIVE_CLASSIFICATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        if kw in name_lower or kw.replace('_', '') in name_lower:
            return kw, level
    return name_lower, "LOW"


def scan_sensitive_data(repository: str, filepath: str, code: str, language: Language) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')
    seen_vars = set()

    for i, line in enumerate(lines, start=1):
        line_clean = line.strip()
        # Skip pure comments
        if line_clean.startswith(('#', '//', '/*', '*')):
            continue

        matched_names = []

        for match in SENSITIVE_VAR_PATTERN.finditer(line):
            matched_names.append(match.group('name'))

        if language == Language.JAVA:
            for match in JAVA_SENSITIVE_FIELD_PATTERN.finditer(line):
                cand = match.group('name')
                _, level = classify_identifier(cand)
                if level in ("CRITICAL", "HIGH", "MEDIUM"):
                    matched_names.append(cand)

        elif language == Language.GO:
            for match in GO_SENSITIVE_FIELD_PATTERN.finditer(line):
                cand = match.group('name')
                _, level = classify_identifier(cand)
                if level in ("CRITICAL", "HIGH", "MEDIUM"):
                    matched_names.append(cand)

        for name in matched_names:
            var_key = f"{filepath}:{name.lower()}"
            if var_key in seen_vars:
                continue
            seen_vars.add(var_key)

            kw, classification = classify_identifier(name)
            findings.append(FindingRecord(
                asset_type=AssetType.SENSITIVE_DATA,
                repository=repository,
                file=filepath,
                line=i,
                language=language,
                api=f"data:{name}",
                operation="sensitive_data_declaration",
                evidence=line_clean,
                confidence=0.9,
                extra={
                    "name": name,
                    "keyword": kw,
                    "classification": classification
                }
            ))

    return findings
