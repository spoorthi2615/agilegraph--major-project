from src.scanners.java.scanner import scan_java_code
from src.scanners.common.enums import AssetType

def test_java_scanner_rsa():
    code = 'import java.security.KeyPairGenerator;\nKeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");'
    findings = scan_java_code("repo", "Test.java", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "RSA"
    assert usage.operation == "key_generation"

def test_java_scanner_aes():
    code = 'import javax.crypto.Cipher;\nCipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");'
    findings = scan_java_code("repo", "Test.java", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert "AES" in usage.algorithm
    assert usage.operation == "encryption"

def test_java_scanner_hashing():
    code = 'import java.security.MessageDigest;\nMessageDigest md = MessageDigest.getInstance("SHA-256");'
    findings = scan_java_code("repo", "Test.java", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "SHA-256"
    assert usage.operation == "hashing"

def test_java_scanner_unrelated():
    code = 'public class Main { public static void main(String[] args) { System.out.println("Hello"); } }'
    findings = scan_java_code("repo", "Test.java", code)
    assert len(findings) == 0

def test_java_scanner_malformed():
    code = 'this is not java code but cipher.getinstance("AES") might be found'
    # It should not fail, just return no imports and maybe a usage if it matches regex
    findings = scan_java_code("repo", "Test.java", code)
    assert len(findings) == 0 # because "cipher.getinstance" is lowercase and regex is case-sensitive
