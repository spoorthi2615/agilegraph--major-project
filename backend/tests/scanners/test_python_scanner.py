"""
Python scanner regression tests.

Covers:
  - Aliased imports (sha1 as s, DES as D, generate_private_key as gpk)
  - RSA.generate(bits=1024) — keyword argument
  - EC key generation → ecdsa, not rsa
  - DSA key generation → dsa, not rsa
  - DES3 → 3des family
  - Numeric key sizes only (no key material in key_size)
  - hashlib.new("sha256") string literal resolution
  - from hashlib import sha1 as s; s(b"data")
"""
import pytest
from src.scanners.python.scanner import scan_python_code
from src.scanners.common.enums import AssetType


def crypto_findings(code: str):
    """Run scanner and return only CRYPTO_USAGE findings."""
    all_findings = scan_python_code("test", "test.py", code)
    return [f for f in all_findings if f.asset_type == AssetType.CRYPTO_USAGE]


def algorithms(code: str):
    return {f.algorithm for f in crypto_findings(code)}


# ── Aliased imports ───────────────────────────────────────────────────────────

def test_sha1_alias():
    code = """
from hashlib import sha1 as s
s(b"data")
"""
    algs = algorithms(code)
    assert "sha1" in algs, f"Expected sha1, got {algs}"


def test_des_alias():
    code = """
from Crypto.Cipher import DES as D
D.new(b'12345678', D.MODE_ECB)
"""
    algs = algorithms(code)
    assert "des" in algs, f"Expected des, got {algs}"


def test_generate_private_key_alias():
    code = """
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key as gpk
gpk(65537, 2048)
"""
    findings = crypto_findings(code)
    # Should detect rsa key generation
    rsa_finds = [f for f in findings if "rsa" in (f.algorithm or "").lower()]
    assert rsa_finds, f"Expected rsa finding from gpk alias, got: {[f.algorithm for f in findings]}"


# ── RSA key generation ─────────────────────────────────────────────────────────

def test_rsa_generate_bits_kwarg():
    code = """
from Crypto.PublicKey import RSA
key = RSA.generate(bits=1024)
"""
    findings = crypto_findings(code)
    rsa = [f for f in findings if f.algorithm == "rsa"]
    assert rsa, "RSA.generate should be detected"
    key_sizes = [f.extra.get("key_size") for f in rsa if f.extra]
    assert 1024 in key_sizes, f"key_size=1024 expected, got {key_sizes}"


def test_rsa_generate_positional():
    code = """
from Crypto.PublicKey import RSA
key = RSA.generate(2048)
"""
    findings = crypto_findings(code)
    rsa = [f for f in findings if f.algorithm == "rsa"]
    assert rsa
    key_sizes = [f.extra.get("key_size") for f in rsa if f.extra]
    assert 2048 in key_sizes, f"key_size=2048 expected, got {key_sizes}"


# ── EC key generation — must NOT be labelled RSA ─────────────────────────────

def test_ec_keygen_is_ecdsa_not_rsa():
    code = """
from Crypto.PublicKey import ECC
key = ECC.generate(curve="P-256")
"""
    findings = crypto_findings(code)
    algs = {f.algorithm for f in findings}
    assert "ecdsa" in algs or "ec" in algs, f"EC keygen should produce ecdsa/ec, got {algs}"
    assert "rsa" not in algs, f"EC keygen must NOT be labelled rsa, got {algs}"


def test_ec_from_cryptography():
    code = """
from cryptography.hazmat.primitives.asymmetric import ec
private_key = ec.generate_private_key(ec.SECP256R1())
"""
    findings = crypto_findings(code)
    algs = {f.algorithm for f in findings}
    assert "ecdsa" in algs or "ecdh" in algs or "ec" in algs, f"EC keygen not detected: {algs}"
    assert "rsa" not in algs, f"EC keygen labelled as RSA: {algs}"


# ── DSA key generation ────────────────────────────────────────────────────────

def test_dsa_keygen_is_dsa_not_rsa():
    code = """
from Crypto.PublicKey import DSA
key = DSA.generate(2048)
"""
    findings = crypto_findings(code)
    algs = {f.algorithm for f in findings}
    assert "dsa" in algs, f"DSA keygen should produce dsa, got {algs}"
    assert "rsa" not in algs, f"DSA keygen must NOT be labelled rsa, got {algs}"


# ── DES3 ──────────────────────────────────────────────────────────────────────

def test_des3_detected():
    code = """
from Crypto.Cipher import DES3
cipher = DES3.new(key, DES3.MODE_ECB)
"""
    findings = crypto_findings(code)
    algs = {f.algorithm for f in findings}
    assert "3des" in algs or "des3" in algs, f"DES3 cipher not detected: {algs}"


# ── hashlib.new string literal ────────────────────────────────────────────────

def test_hashlib_new_sha256():
    code = """
import hashlib
h = hashlib.new("sha256")
"""
    algs = algorithms(code)
    assert "sha256" in algs, f"hashlib.new('sha256') must produce sha256, got {algs}"


def test_hashlib_new_md5():
    code = """
import hashlib
h = hashlib.new("MD5")
"""
    algs = algorithms(code)
    assert "md5" in algs


# ── Key size must be numeric only ────────────────────────────────────────────

def test_des_new_key_material_not_in_key_size():
    """DES.new(b'12345678', ...) — the key material b'12345678' must NOT become key_size."""
    code = """
from Crypto.Cipher import DES
cipher = DES.new(b'12345678', DES.MODE_ECB)
"""
    findings = crypto_findings(code)
    for f in findings:
        ks = (f.extra or {}).get("key_size")
        assert ks is None or isinstance(ks, (int, float)), \
            f"key_size must be numeric, got {ks!r} (possible key material leak)"


# ── hashlib direct import and call ───────────────────────────────────────────

def test_hashlib_direct_md5():
    code = """
import hashlib
h = hashlib.md5()
"""
    algs = algorithms(code)
    assert "md5" in algs


def test_hashlib_alias_sha256():
    code = """
import hashlib as hl
h = hl.sha256()
"""
    algs = algorithms(code)
    assert "sha256" in algs, f"hashlib alias must resolve sha256, got {algs}"


# ── rsa library ───────────────────────────────────────────────────────────────

def test_rsa_newkeys():
    code = """
import rsa
pub, priv = rsa.newkeys(512)
"""
    findings = crypto_findings(code)
    rsa_finds = [f for f in findings if f.algorithm == "rsa"]
    assert rsa_finds, "rsa.newkeys must produce rsa finding"
    key_sizes = [f.extra.get("key_size") for f in rsa_finds if f.extra]
    assert 512 in key_sizes
