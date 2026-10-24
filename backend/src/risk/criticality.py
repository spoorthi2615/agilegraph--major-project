from src.risk.factors import FactorValue

CRITICALITY_MAP = {
    "LOW": 0.25,
    "MEDIUM": 0.5,
    "HIGH": 0.75,
    "CRITICAL": 1.0,
    "UNKNOWN": None
}

# Explicit markers for demonstrably security-critical implementation paths
CORE_SECURITY_PATH_MARKERS = (
    "/hazmat/primitives/",
    "/hazmat/bindings/",
    "/ciphers/",
    "/asymmetric/",
    "/keystore/",
    "/keys/",
    "/signing/",
    "/keyagreement/",
    "/signer",
    "/verifier",
    "/auth/",
    "/jwt",
    "/crypto/rsa",
    "/crypto/ecdsa",
    "/crypto/aes",
    "/crypto/cipher",
    "/crypto/tls",
    "/crypto/sha",
)

CORE_SECURITY_FILENAMES = (
    "cipher.py", "ciphers.py", "aes.py", "rsa.py", "ecdsa.py", "dsa.py",
    "hmac.py", "sha256.py", "sha512.py", "signer.py", "verifier.py", "keys.py",
    "Cipher.java", "Signature.java", "KeyPairGenerator.java", "KeyGenerator.java",
    "KeyAgreement.java", "SecretKeyFactory.java", "DefaultJwtParser.java",
    "rsa.go", "ecdsa.go", "aes.go", "cipher.go", "signature.go", "tls.go", "signer.go"
)


def extract_asset_criticality(metadata: dict, file_path: str = None, in_degree: int = 0) -> FactorValue:
    """
    Three-tier conservative proxy for asset criticality per Synopsis 5.4:
      - 1.00: Explicit metadata (CRITICAL)
      - 0.75: Demonstrably security-critical implementation modules (core ciphers, key gens, signing)
      - 0.50: Central shared dependency / utility modules (in-degree >= 3)
      - 0.25: Non-production test fixtures, mocks, examples
      - None: Insufficient evidence (uncertain, preserved as None for renormalization/conservative policy)
    """
    # 1. Check explicitly provided business/service/system criticality
    crit = metadata.get("business_criticality") or metadata.get("service_criticality") or metadata.get("system_criticality")
    if crit:
        crit = str(crit).upper()
        if crit in CRITICALITY_MAP and crit != "UNKNOWN":
            return FactorValue(value=CRITICALITY_MAP[crit], source="explicit metadata", confidence=1.0)

    # 2. Data-backed role inference from file path and graph topology
    if file_path:
        fp_lower = "/" + file_path.lower().replace('\\', '/').lstrip('/')
        
        # Non-production / test / example proxy (0.25)
        if any(t in fp_lower for t in ("/tests/", "/test/", "test_", "_test.", "testcase", "mock", "/examples/", "/example/", "/samples/", "/sample/")):
            return FactorValue(value=0.25, source="inferred non-production asset (test/example proxy)", confidence=0.9)

        # Demonstrably security-critical module proxy (0.75)
        # Tightened to avoid over-assigning 0.75 to entire cryptographic repositories
        is_security_path = any(m in fp_lower for m in CORE_SECURITY_PATH_MARKERS)
        is_security_filename = any(fp_lower.endswith("/" + fn.lower()) or fp_lower.endswith(fn.lower()) for fn in CORE_SECURITY_FILENAMES)
        
        if is_security_path or is_security_filename:
            return FactorValue(value=0.75, source=f"inferred security-critical module proxy: {file_path}", confidence=0.8)

        # Shared dependency / central utility proxy (0.50)
        if in_degree >= 3:
            return FactorValue(value=0.50, source=f"inferred shared dependency module proxy (in-degree={in_degree})", confidence=0.7)
            
    # Default policy: Insufficient evidence (epistemic uncertainty preserved)
    return FactorValue(value=None, source="not provided", confidence=0.0)
