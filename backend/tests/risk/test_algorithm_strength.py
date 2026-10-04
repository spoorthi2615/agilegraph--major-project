"""
Regression tests for the algorithm strength classifier.

Tests specifically target:
  - No unsafe substring matching (destination ≠ DES, selectedAlg ≠ SHA1, etc.)
  - Compound strings (SHA256withRSA → RSA risk, not SHA256 risk)
  - PQC algorithms are NOT flagged as vulnerable
  - 3DES variants all normalize correctly
  - ARCFOUR / ARC4 normalize to rc4
  - Padding modes strip correctly
  - Known-good algorithms stay strong
  - Unrecognized → None (never 0.0)
"""
import pytest
from src.risk.algorithm_strength import extract_crypto_weakness


# ── Canonical weak algorithms ───────────────────────────────────────────────
@pytest.mark.parametrize("alg,expected_min", [
    ("md5",          0.9),
    ("MD5",          0.9),
    ("sha1",         0.9),
    ("SHA1",         0.9),
    ("SHA-1",        0.9),
    ("des",          0.9),
    ("DES",          0.9),
    ("rc4",          0.9),
    ("RC4",          0.9),
    ("arc4",         0.9),
    ("ARCFOUR",      0.9),
    ("blowfish",     0.7),
    ("rsa",          0.8),
    ("RSA",          0.8),
    ("dsa",          0.8),
    ("DSA",          0.8),
    ("ecdsa",        0.8),
    ("ECDSA",        0.8),
    ("ec",           0.8),
])
def test_weak_algorithms_flagged(alg, expected_min):
    result = extract_crypto_weakness(alg)
    assert result.value is not None, f"{alg!r} should be rated, got None"
    assert result.value >= expected_min, f"{alg!r}: expected >= {expected_min}, got {result.value}"


# ── 3DES variants ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("alg", ["DESede", "TripleDES", "3DES", "DES3", "desede"])
def test_3des_variants(alg):
    result = extract_crypto_weakness(alg)
    assert result.value is not None, f"{alg!r} should be rated"
    assert result.value >= 0.7, f"{alg!r}: expected >= 0.7, got {result.value}"


# ── Compound algorithm strings ────────────────────────────────────────────────
def test_sha256withrsa_is_rsa_risk():
    """SHA256withRSA is an RSA signature — risk is from RSA, not SHA256."""
    r = extract_crypto_weakness("SHA256withRSA")
    assert r.value is not None
    # RSA is PQ-vulnerable (0.9), SHA-256 is strong (0.1).
    # Compound takes the "with" suffix → rsa
    assert r.value >= 0.8, f"SHA256withRSA should carry RSA-level risk, got {r.value}"


def test_sha512withrsa_is_rsa_risk():
    r = extract_crypto_weakness("SHA512withRSA")
    assert r.value is not None and r.value >= 0.8


def test_sha256withecdsa_is_ecdsa_risk():
    r = extract_crypto_weakness("SHA256withECDSA")
    assert r.value is not None and r.value >= 0.8


def test_rsa_oaep_padding_is_rsa_risk():
    """RSA/ECB/OAEPWithSHA-256AndMGF1Padding — base is RSA."""
    r = extract_crypto_weakness("RSA/ECB/OAEPWithSHA-256AndMGF1Padding")
    assert r.value is not None and r.value >= 0.8


def test_aes_cbc_padding_is_aes_risk():
    r = extract_crypto_weakness("AES/CBC/PKCS5Padding")
    assert r.value is not None
    assert r.value == pytest.approx(0.3, abs=0.05)


def test_blowfish_ecb_is_blowfish():
    r = extract_crypto_weakness("Blowfish/ECB/PKCS5Padding")
    assert r.value is not None and r.value >= 0.7


def test_des_ecb_pkcs5():
    r = extract_crypto_weakness("DES/ECB/PKCS5Padding")
    assert r.value is not None and r.value >= 0.9


def test_diffiehellman():
    r = extract_crypto_weakness("DiffieHellman")
    assert r.value is not None and r.value >= 0.8


# ── PQC algorithms — must NOT be vulnerable ──────────────────────────────────
@pytest.mark.parametrize("alg", [
    "ML-DSA-65",
    "ML-DSA-44",
    "ML-KEM-512",
    "ML-KEM-768",
    "SLH-DSA-SHA2-128s",
    "SLH-DSA-SHAKE-256f",
    "Kyber",
    "Dilithium",
    "Falcon",
])
def test_pqc_algorithms_not_vulnerable(alg):
    r = extract_crypto_weakness(alg)
    assert r.value is not None, f"{alg!r} should be rated (as strong/PQC), got None"
    assert r.value < 0.1, f"{alg!r} is PQC — risk should be < 0.1, got {r.value}"


# ── Identifiers that must NOT match any algorithm ────────────────────────────
@pytest.mark.parametrize("non_alg", [
    "destination",    # must not match "des"
    "selectedAlg",    # must not match "sha1" etc.
    "cipherSpec",     # not an algorithm name itself
    "myDesiredValue", # contains "des" but is not DES
    "echoServer",     # contains "ec" but is not EC
    "classicrsa",     # is not a standard identifier
    "DESCRIPTION",    # contains DES
    "process",        # contains "rsa"? No, but let's test
    "base64",         # harmless; no crypto family
    "SHA256Util",     # a class name, not an algorithm
])
def test_non_algorithm_identifiers_are_unrated(non_alg):
    r = extract_crypto_weakness(non_alg)
    assert r.value is None, (
        f"{non_alg!r} is NOT a crypto algorithm — should be unrated (None), got {r.value}"
    )


# ── Strong algorithms ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("alg,expected_max", [
    ("sha256",   0.2),
    ("SHA-256",  0.2),
    ("sha512",   0.1),
    ("SHA-512",  0.1),
    ("aes",      0.4),
    ("chacha20", 0.1),
    ("kyber",    0.0),
])
def test_strong_algorithms_low_risk(alg, expected_max):
    r = extract_crypto_weakness(alg)
    assert r.value is not None, f"{alg!r} should be rated"
    assert r.value <= expected_max, f"{alg!r}: expected <= {expected_max}, got {r.value}"


# ── JWT Algorithms ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("alg,expected_min", [
    ("none",   1.0),
    ("HS256",  0.0),  # mapped to sha256 (0.1), so expected_min won't work perfectly if it's 0.1. Let's use exact checks
])
def test_jwt_algorithms(alg, expected_min):
    # This parametrization is just a placeholder, let's write them individually.
    pass

def test_jwt_none_is_critical_risk():
    r = extract_crypto_weakness("none")
    assert r.value == pytest.approx(1.0, abs=0.01)

def test_jwt_hs256_is_sha256_risk():
    r = extract_crypto_weakness("HS256")
    assert r.value == pytest.approx(0.1, abs=0.01)

def test_jwt_hs512_is_sha512_risk():
    r = extract_crypto_weakness("HS512")
    assert r.value == pytest.approx(0.05, abs=0.01)

def test_jwt_rs256_is_rsa_risk():
    r = extract_crypto_weakness("RS256")
    assert r.value == pytest.approx(0.9, abs=0.01)

def test_jwt_es256_is_ecdsa_risk():
    r = extract_crypto_weakness("ES256")
    assert r.value == pytest.approx(0.9, abs=0.01)



# ── Unrecognized → None, not 0.0 ────────────────────────────────────────────
@pytest.mark.parametrize("alg", [
    "GREASE_ALGO",
    "XChaCha20-Poly1305",   # not in map yet
    "ed25519",              # not in current map
    "",
])
def test_unrecognized_returns_none_not_zero(alg):
    r = extract_crypto_weakness(alg)
    assert r.value is None, f"{alg!r} should be unrated (None), not {r.value}"
    assert r.value != 0.0   # 0.0 would mean "perfectly safe", which is wrong


# ── RSA key-size modifiers ────────────────────────────────────────────────────
def test_rsa_1024_max_risk():
    r = extract_crypto_weakness("rsa", key_size=1024)
    assert r.value == pytest.approx(1.0, abs=0.01)


def test_rsa_2048_standard():
    r = extract_crypto_weakness("rsa", key_size=2048)
    assert r.value == pytest.approx(0.9, abs=0.01)


def test_rsa_4096_reduced_risk():
    r = extract_crypto_weakness("rsa", key_size=4096)
    assert r.value == pytest.approx(0.8, abs=0.01)


def test_rsa_1024_vs_4096_different():
    r1 = extract_crypto_weakness("rsa", key_size=1024)
    r2 = extract_crypto_weakness("rsa", key_size=4096)
    assert r1.value != r2.value, "RSA-1024 and RSA-4096 must not receive the same score"
