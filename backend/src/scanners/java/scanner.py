import re
from typing import List, Optional
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

JAVA_IMPORT_PATTERN = re.compile(
    r'import\s+(java\.security\.[a-zA-Z0-9_.*]+|javax\.crypto\.[a-zA-Z0-9_.*]+|org\.bouncycastle\.[a-zA-Z0-9_.*]+);'
)

# Capture class=api, algorithm string
JAVA_ALGO_PATTERN = re.compile(
    r'\b(Cipher|MessageDigest|KeyPairGenerator|KeyGenerator|Signature|Mac|KeyAgreement|KeyFactory)\b'
    r'\.getInstance\s*\(\s*([^)]+)\s*\)'
)

# Variable declaration: <Type> <varName> = <class>.getInstance(...)
# We track variable name → crypto class name
JAVA_VARNAME_PATTERN = re.compile(
    r'\b(Cipher|MessageDigest|KeyPairGenerator|KeyGenerator|Signature|Mac|KeyAgreement|KeyFactory)\b'
    r'\s+(\w+)\s*='
)

# String variable declarations to resolve variables in getInstance
# Matches local variables and static final constants
JAVA_STRING_VAR_PATTERN = re.compile(r'\b(?:private\s+|public\s+|static\s+|final\s+)*String\s+(\w+)\s*=\s*"([^"]+)"\s*;')

# jjwt SignatureAlgorithm enum usage
JAVA_JJWT_ENUM_PATTERN = re.compile(r'\bSignatureAlgorithm\.([A-Z0-9_]+)\b')

# .initialize(N) — we need the variable it's called on
JAVA_INIT_PATTERN = re.compile(r'\b(\w+)\.initialize\s*\(\s*(\d+)\s*\)')


def scan_java_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')

    # Map: variable_name → most-recent FindingRecord with operation==key_generation
    # so we can do context-aware key-size association.
    keygen_vars: dict[str, FindingRecord] = {}

    # Map: String variable name -> value
    string_vars: dict[str, str] = {}

    for i, line in enumerate(lines):
        line_num = i + 1

        # Track string variables
        str_match = JAVA_STRING_VAR_PATTERN.search(line)
        if str_match:
            string_vars[str_match.group(1)] = str_match.group(2)

        # ── imports ─────────────────────────────────────────────────────────
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

        # ── variable declarations (track which var holds which keygen) ───────
        varname_match = JAVA_VARNAME_PATTERN.search(line)

        # ── algorithm usages ─────────────────────────────────────────────────
        usage_match = JAVA_ALGO_PATTERN.search(line)
        if usage_match:
            api_class = usage_match.group(1)
            algorithm_raw = usage_match.group(2).strip()

            if algorithm_raw.startswith('"') and algorithm_raw.endswith('"'):
                algorithm = algorithm_raw.strip('"')
            elif algorithm_raw in string_vars:
                algorithm = string_vars[algorithm_raw]
            else:
                algorithm = "UNKNOWN_ALGORITHM"

            operation = (
                "encryption"     if "Cipher"          in api_class else
                "hashing"        if "MessageDigest"   in api_class or "Mac" in api_class else
                "key_generation" if "Key"             in api_class else
                "signature"
            )

            finding = FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                api=f"{api_class}.getInstance()",
                algorithm=algorithm,
                operation=operation,
                evidence=line.strip(),
                confidence=0.9,
                extra={}
            )
            findings.append(finding)

            # Track which variable holds this keygen finding
            if operation == "key_generation" and varname_match:
                var = varname_match.group(2)
                keygen_vars[var] = finding

        # ── initialize(N) — associate with the *specific* variable ──────────
        for init_match in JAVA_INIT_PATTERN.finditer(line):
            var = init_match.group(1)
            key_size = int(init_match.group(2))

            if var in keygen_vars:
                # Only associate with that specific variable's finding
                f = keygen_vars[var]
                if not f.extra:
                    f.extra = {}
                if "key_size" not in f.extra:
                    f.extra["key_size"] = key_size
                    f.evidence = f"{f.evidence} ... Key size {key_size}"
            # If var is not a tracked keygen variable, we ignore the initialize() call.
            # This prevents "pool.initialize(8)" from attaching to an unrelated RSA finding.
            
        # ── jjwt enum algorithm usages ─────────────────────────────────────
        for enum_match in JAVA_JJWT_ENUM_PATTERN.finditer(line):
            algo = enum_match.group(1)
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                api="SignatureAlgorithm",
                algorithm=algo,
                operation="signature",
                evidence=line.strip(),
                confidence=0.9,
                extra={}
            ))

    return findings
