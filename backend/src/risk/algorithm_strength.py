from src.risk.factors import FactorValue

# INITIAL HEURISTIC MAPPING - NOT FINAL WEIGHTS
# Represents post-quantum migration risk in this project's context,
# not a generic statement that every use is currently universally weak.
# 1.0 = Highly vulnerable to quantum/classical attacks
# 0.5 = Transitioning/Medium weakness
# 0.0 = Quantum resistant / currently strong

# --- Canonical algorithm families ---
# Maps canonical family name → base weakness score
CANONICAL_FAMILY_MAP = {
    # Hash functions
    "md5":        1.0,
    "sha1":       1.0,
    "sha256":     0.1,
    "sha384":     0.1,
    "sha512":     0.05,
    # Symmetric ciphers
    "des":        1.0,
    "3des":       0.8,   # normalized form for DES3/DESede/TripleDES
    "aes":        0.3,
    "blowfish":   0.8,
    "rc4":        1.0,
    "arc4":       1.0,
    "arcfour":    1.0,
    "chacha20":   0.05,
    "none":       1.0,   # Unsigned JWTs or explicitly no algorithm (Signature bypass)
    # Asymmetric
    "rsa":        0.9,
    "dsa":        0.9,
    "ecdsa":      0.9,
    "ecdh":       0.9,
    "ec":         0.9,
    "dh":         0.9,
    "diffiehellman": 0.9,
    # PQC (NIST standardised) — strong
    "kyber":      0.0,
    "dilithium":  0.0,
    "falcon":     0.0,
    "sphincs":    0.0,
    # NIST PQC final names (ML-DSA / ML-KEM / SLH-DSA) — strong
    "mlkem":      0.0,
    "mldsa":      0.0,
    "slhdsa":     0.0,
    "hqc":        0.0,
    "bike":       0.0,
}

# Maps raw strings that appear verbatim in scanner output → canonical family
# These are explicit normalizations only — no substring guessing.
ALIAS_MAP = {
    # 3DES variants
    "desede":        "3des",
    "tripledes":     "3des",
    "3des":          "3des",
    "des3":          "3des",
    # RC4 variants
    "arcfour":       "rc4",
    "arc4":          "rc4",
    # DH variants
    "diffiehellman": "dh",
    "diffie-hellman":"dh",
    # SHA variants
    "sha-1":         "sha1",
    "sha-256":       "sha256",
    "sha-384":       "sha384",
    "sha-512":       "sha512",
    # JWT algorithms
    "hs256":         "sha256",
    "hs384":         "sha384",
    "hs512":         "sha512",
    "rs256":         "rsa",
    "rs384":         "rsa",
    "rs512":         "rsa",
    "es256":         "ecdsa",
    "es384":         "ecdsa",
    "es512":         "ecdsa",
    "ps256":         "rsa",
    "ps384":         "rsa",
    "ps512":         "rsa",
    # EC variants
    "ec":            "ec",
    # PQC — NIST final names (strip hyphens and digits to get family)
    # These are *prefix* matches handled explicitly below.
}

# Compound algorithm strings like "SHA256withRSA" encode TWO primitives.
# We parse these to extract the *signature* family (the part after "with").
# The risk of a signature scheme is determined by its asymmetric component.
_WITH_PATTERN_SEPARATOR = "with"

def _normalize_raw(raw: str) -> str:
    """Lowercase and strip hyphens/underscores/spaces for matching."""
    return raw.lower().replace("-", "").replace("_", "").replace(" ", "")


def _extract_family(raw: str) -> str | None:
    """
    Map a raw algorithm string to its canonical family.

    Returns one of the keys in CANONICAL_FAMILY_MAP, or None if unknown.

    Strategy (in order, no fallback substring guessing):
    1. Exact alias match (lowercased, hyphen/underscore stripped).
    2. Compound "XwithY" → take Y component → recurse.
    3. PQC family prefix match (ML-KEM, ML-DSA, SLH-DSA, SPHINCS+…).
    4. Exact match in canonical family map.
    5. Common suffix patterns for OAEP/padding modes → strip and recurse.
    6. None (unknown / unrated).
    """
    if not raw:
        return None

    norm = _normalize_raw(raw)

    # Step 1: Alias map (handles desede, tripledes, arcfour, sha-1, etc.)
    if norm in ALIAS_MAP:
        return ALIAS_MAP[norm]

    # Step 2: Exact canonical family
    if norm in CANONICAL_FAMILY_MAP:
        return norm

    # Step 3: Slash-delimited mode string
    # e.g. "rsa/ecb/oaepwithsha-256andmgf1padding"
    # After stripping the parts before "/" we might find "rsa"
    if "/" in norm:
        base = norm.split("/")[0]
        return _extract_family(base)

    # Step 4: Compound "SHA256withRSA", "SHA512withECDSA", etc.
    #   The asymmetric component (after "with") drives the risk.
    if "with" in norm:
        _, _, suffix = norm.partition("with")
        # suffix is e.g. "rsa", "ecdsa"
        return _extract_family(suffix)   # recurse (suffix is already stripped)

    # Step 5: PQC family prefixes (ML-KEM-512 → mlkem, SLH-DSA-SHA2-128s → slhdsa)
    for pqc_prefix in ("mlkem", "mldsa", "slhdsa", "sphincsplus", "falcon", "kyber", "dilithium", "hqc", "bike"):
        if norm.startswith(pqc_prefix):
            return pqc_prefix

    # Step 6: Unknown
    return None


def extract_crypto_weakness(
    algorithm: str,
    weakness_map: dict = None,
    key_size: int = None,
) -> FactorValue:
    """
    Return a FactorValue for the given algorithm string.

    FactorValue.value is None when the algorithm is unrecognized (unrated),
    not when it is absent.  Callers must not treat None as 0.0 risk.
    """
    if weakness_map is None:
        weakness_map = CANONICAL_FAMILY_MAP

    if not algorithm:
        return FactorValue(value=None, source="algorithm unknown", confidence=0.0)

    family = _extract_family(algorithm)

    if family is None:
        return FactorValue(
            value=None,
            source=f"unrecognized algorithm ({algorithm})",
            confidence=0.0,
        )

    base_weakness = weakness_map.get(family, None)
    if base_weakness is None:
        return FactorValue(
            value=None,
            source=f"unrecognized algorithm family ({family})",
            confidence=0.0,
        )

    # Key-size adjustment for RSA
    if family == "rsa" and key_size is not None:
        if key_size <= 1024:
            return FactorValue(
                value=1.0,
                source=f"algorithm classification (rsa-{key_size})",
                confidence=0.9,
            )
        elif key_size >= 4096:
            return FactorValue(
                value=0.8,
                source=f"algorithm classification (rsa-{key_size})",
                confidence=0.9,
            )
        else:
            return FactorValue(
                value=0.9,
                source=f"algorithm classification (rsa-{key_size})",
                confidence=0.9,
            )

    return FactorValue(
        value=base_weakness,
        source=f"algorithm classification ({family})",
        confidence=0.9,
    )
