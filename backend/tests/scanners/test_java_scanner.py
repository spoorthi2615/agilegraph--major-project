"""
Java scanner regression tests.

Covers:
  - Context-aware key-size association (variable tracking)
  - RSA + EC in same file → each gets its own key size
  - pool.initialize(8) must not fabricate an RSA-8 finding
  - SHA-1 → sha-1 (exact algorithm preserved)
  - Signature algorithms (SHA256withRSA)
"""
import pytest
from src.scanners.java.scanner import scan_java_code
from src.scanners.common.enums import AssetType


def findings_by_algo(findings, algo_lower):
    return [f for f in findings if f.algorithm and f.algorithm.lower() == algo_lower]


def test_rsa_ec_separate_key_sizes():
    """
    RSA keygen initialized to 4096 and EC keygen initialized to 256 in the same file
    must NOT share key sizes.
    """
    code = """
import java.security.KeyPairGenerator;
public class Test {
    public void generate() throws Exception {
        KeyPairGenerator rsaGen = KeyPairGenerator.getInstance("RSA");
        rsaGen.initialize(4096);

        KeyPairGenerator ecGen = KeyPairGenerator.getInstance("EC");
        ecGen.initialize(256);
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    rsa = [f for f in findings if f.algorithm and f.algorithm.upper() == "RSA" and f.operation == "key_generation"]
    ec  = [f for f in findings if f.algorithm and f.algorithm.upper() == "EC"  and f.operation == "key_generation"]

    assert rsa, "RSA keygen finding must exist"
    assert ec,  "EC keygen finding must exist"

    rsa_size = rsa[0].extra.get("key_size") if rsa[0].extra else None
    ec_size  = ec[0].extra.get("key_size")  if ec[0].extra  else None

    assert rsa_size == 4096, f"RSA must receive key_size=4096, got {rsa_size}"
    assert ec_size  == 256,  f"EC must receive key_size=256, got {ec_size}"


def test_unrelated_initialize_does_not_attach_to_rsa():
    """
    pool.initialize(8) must not attach to an RSA KeyPairGenerator finding
    that appeared earlier in the file.
    """
    code = """
import java.security.KeyPairGenerator;
public class Test {
    public void test() throws Exception {
        KeyPairGenerator rsaGen = KeyPairGenerator.getInstance("RSA");
        rsaGen.initialize(2048);

        SomeThreadPool pool = new SomeThreadPool();
        pool.initialize(8);  // NOT a crypto key size
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    rsa = [f for f in findings if f.algorithm and f.algorithm.upper() == "RSA" and f.operation == "key_generation"]
    assert rsa, "RSA keygen must be found"
    rsa_size = rsa[0].extra.get("key_size") if rsa[0].extra else None
    assert rsa_size == 2048, f"RSA key_size should be 2048, not 8. Got {rsa_size}"


def test_sha1_algorithm_preserved():
    code = """
import java.security.MessageDigest;
public class Test {
    public void test() throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-1");
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    crypto = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert any(f.algorithm == "SHA-1" for f in crypto), "SHA-1 algorithm must be preserved exactly"


def test_des_and_aes_in_same_file():
    code = """
import javax.crypto.Cipher;
public class Test {
    public void test() throws Exception {
        Cipher c1 = Cipher.getInstance("DES/ECB/PKCS5Padding");
        Cipher c2 = Cipher.getInstance("AES/CBC/PKCS5Padding");
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    algos = [f.algorithm for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert "DES/ECB/PKCS5Padding" in algos
    assert "AES/CBC/PKCS5Padding" in algos


def test_signature_algorithm():
    code = """
import java.security.Signature;
public class Test {
    public void test() throws Exception {
        Signature sig = Signature.getInstance("SHA256withRSA");
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    sig_findings = [f for f in findings if f.operation == "signature"]
    assert sig_findings, "Signature finding must be detected"
    assert any(f.algorithm == "SHA256withRSA" for f in sig_findings)


def test_rsa_keygen_no_init_no_key_size():
    """KeyPairGenerator without initialize must not have a key_size."""
    code = """
import java.security.KeyPairGenerator;
public class Test {
    public void test() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    rsa = [f for f in findings if f.algorithm and "RSA" in f.algorithm.upper() and f.operation == "key_generation"]
    assert rsa
    rsa_size = rsa[0].extra.get("key_size") if rsa[0].extra else None
    assert rsa_size is None, f"No initialize() → key_size should be None, got {rsa_size}"
