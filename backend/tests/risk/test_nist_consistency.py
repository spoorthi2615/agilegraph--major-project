"""
Unit tests validating AgileGraph crypto_weakness ordering against NIST standards:
FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), NIST IR 8547, and SP 800-131A Rev. 2.
"""

import pytest
from src.risk.algorithm_strength import extract_crypto_weakness, CANONICAL_FAMILY_MAP

def test_pqc_algorithms_are_zero_weakness():
    pqc_algorithms = ["mlkem", "mldsa", "slhdsa", "kyber", "dilithium", "falcon"]
    for algo in pqc_algorithms:
        factor = extract_crypto_weakness(algo)
        assert factor.value == 0.0, f"PQC algorithm {algo} must have 0.0 weakness score"

def test_shor_vulnerable_algorithms_have_critical_weakness():
    # Asymmetric public key primitives vulnerable to polynomial-time Shor's attack
    shor_vulnerable = ["rsa", "ecdsa", "ed25519", "dsa", "dh", "ecdh", "x25519"]
    for algo in shor_vulnerable:
        factor = extract_crypto_weakness(algo)
        assert factor.value == 0.9, f"Shor-vulnerable algorithm {algo} must have 0.9 weakness score"

def test_legacy_broken_algorithms_have_maximum_weakness():
    broken = ["md5", "sha1", "des", "rc4", "arc4", "none"]
    for algo in broken:
        factor = extract_crypto_weakness(algo)
        assert factor.value == 1.0, f"Classically broken algorithm {algo} must have 1.0 weakness score"

def test_nist_monotonic_risk_ordering():
    # Strict monotonic relationship per NIST review:
    # PQC (0.0) < SHA-512 (0.05) < SHA-256 (0.10) < AES (0.30) < 3DES (0.80) < RSA/ECDSA (0.90) < MD5/DES (1.00)
    pqc_score = extract_crypto_weakness("mlkem").value
    sha512_score = extract_crypto_weakness("sha512").value
    sha256_score = extract_crypto_weakness("sha256").value
    aes_score = extract_crypto_weakness("aes").value
    triple_des_score = extract_crypto_weakness("3des").value
    rsa_score = extract_crypto_weakness("rsa").value
    md5_score = extract_crypto_weakness("md5").value

    assert pqc_score < sha512_score
    assert sha512_score < sha256_score
    assert sha256_score < aes_score
    assert aes_score < triple_des_score
    assert triple_des_score < rsa_score
    assert rsa_score < md5_score
