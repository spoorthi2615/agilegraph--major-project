import re
from typing import List, Optional
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

JAVA_IMPORT_PATTERN = re.compile(
    r'import\s+(java\.security\.[a-zA-Z0-9_.*]+|javax\.crypto\.[a-zA-Z0-9_.*]+|org\.bouncycastle\.[a-zA-Z0-9_.*]+);'
)

# Capture class=api, algorithm string
JAVA_ALGO_PATTERN = re.compile(
    r'\b(Cipher|MessageDigest|KeyPairGenerator|KeyGenerator|Signature|Mac|KeyAgreement|KeyFactory|SecureRandom)\b'
    r'\.getInstance\s*\(\s*([^)]+)\s*\)'
)

# Direct constructor instantiation for SecureRandom
JAVA_SECURE_RANDOM_NEW_PATTERN = re.compile(r'\bnew\s+SecureRandom\s*\(')

# Variable declaration: <Type> <varName> = <class>.getInstance(...)
JAVA_VARNAME_PATTERN = re.compile(
    r'\b(Cipher|MessageDigest|KeyPairGenerator|KeyGenerator|Signature|Mac|KeyAgreement|KeyFactory|SecureRandom)\b'
    r'\s+(\w+)\s*='
)

# String variable declarations to resolve variables in getInstance
# Matches local variables and static final constants
JAVA_STRING_VAR_PATTERN = re.compile(r'\b(?:private\s+|public\s+|static\s+|final\s+)*String\s+(\w+)\s*=\s*"([^"]+)"\s*;')

# jjwt SignatureAlgorithm enum usage
JAVA_JJWT_ENUM_PATTERN = re.compile(r'\bSignatureAlgorithm\.([A-Z0-9_]+)\b')

# .initialize(N) — we need the variable it's called on
JAVA_INIT_PATTERN = re.compile(r'\b(\w+)\.initialize\s*\(\s*(\d+)\s*\)')


def strip_code_comments(line: str, in_block: bool) -> tuple[str, bool]:
    """
    Strips single-line and multi-line comments from a line of Java code,
    respecting string literals and tracking multi-line block comment state.
    Returns (active_code_string, remaining_in_block_boolean).
    """
    out = []
    i = 0
    n = len(line)
    in_quote = None

    while i < n:
        if in_block:
            end_idx = line.find("*/", i)
            if end_idx == -1:
                return "".join(out), True
            else:
                in_block = False
                i = end_idx + 2
        else:
            ch = line[i]
            if in_quote is not None:
                out.append(ch)
                if ch == '\\' and i + 1 < n:
                    out.append(line[i + 1])
                    i += 2
                    continue
                elif ch == in_quote:
                    in_quote = None
                i += 1
            else:
                if ch in ('"', "'"):
                    in_quote = ch
                    out.append(ch)
                    i += 1
                elif line[i:i + 2] == "//":
                    break
                elif line[i:i + 2] == "/*":
                    in_block = True
                    i += 2
                else:
                    out.append(ch)
                    i += 1
    return "".join(out), in_block


def scan_java_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')

    keygen_vars: dict[str, FindingRecord] = {}
    string_vars: dict[str, str] = {}

    in_block_comment = False
    for i, line in enumerate(lines):
        line_num = i + 1
        active_code, in_block_comment = strip_code_comments(line, in_block_comment)
        if not active_code.strip():
            continue

        # Track string variables
        str_match = JAVA_STRING_VAR_PATTERN.search(active_code)
        if str_match:
            string_vars[str_match.group(1)] = str_match.group(2)

        # ── imports ─────────────────────────────────────────────────────────
        import_match = JAVA_IMPORT_PATTERN.search(active_code)
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
        varname_match = JAVA_VARNAME_PATTERN.search(active_code)

        # ── direct new SecureRandom() instantiation ──────────────────────────
        if JAVA_SECURE_RANDOM_NEW_PATTERN.search(active_code):
            findings.append(FindingRecord(
                asset_type=AssetType.CRYPTO_USAGE,
                repository=repository,
                file=filepath,
                line=line_num,
                language=Language.JAVA,
                api="new SecureRandom()",
                algorithm="SecureRandom",
                operation="random",
                evidence=line.strip(),
                confidence=0.9,
                extra={}
            ))

        # ── algorithm usages via getInstance() ──────────────────────────────
        usage_match = JAVA_ALGO_PATTERN.search(active_code)
        if usage_match:
            api_class = usage_match.group(1)
            algorithm_raw = usage_match.group(2).strip()

            if algorithm_raw.startswith('"') and algorithm_raw.endswith('"'):
                algorithm = algorithm_raw.strip('"')
            elif algorithm_raw in string_vars:
                algorithm = string_vars[algorithm_raw]
            else:
                algorithm = "UNKNOWN_ALGORITHM"

            if "Cipher" in api_class:
                operation = "encryption"
            elif "MessageDigest" in api_class or "Mac" in api_class:
                operation = "hashing"
            elif "Key" in api_class:
                operation = "key_generation"
            elif "SecureRandom" in api_class:
                operation = "random"
            else:
                operation = "signature"

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

            if operation == "key_generation" and varname_match:
                var = varname_match.group(2)
                keygen_vars[var] = finding

        # ── initialize(N) — associate with the specific variable ────────────
        for init_match in JAVA_INIT_PATTERN.finditer(active_code):
            var = init_match.group(1)
            key_size = int(init_match.group(2))

            if var in keygen_vars:
                f = keygen_vars[var]
                if not f.extra:
                    f.extra = {}
                if "key_size" not in f.extra:
                    f.extra["key_size"] = key_size
                    f.evidence = f"{f.evidence} ... Key size {key_size}"

        # ── jjwt enum algorithm usages ─────────────────────────────────────
        for enum_match in JAVA_JJWT_ENUM_PATTERN.finditer(active_code):
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
