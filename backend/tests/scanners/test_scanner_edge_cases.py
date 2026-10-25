"""
AgileGraph Scanner Reliability & Edge-Case Regression Tests
============================================================
Verifies:
  - Comments containing crypto keywords are strictly ignored (Python, Java, Go)
  - String literals mentioning algorithms without API invocations produce 0 findings
  - Substring variable collisions (e.g. 'destination', 'md5_cache_key') produce 0 findings
  - Malformed syntax handles errors gracefully without crashing
  - Empty, whitespace-only, and large inputs handle safely
"""

import pytest
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.common.enums import AssetType


# ============================================================================
# 1. Comment Isolation Tests
# ============================================================================

def test_python_commented_code_ignored():
    code = """
# import hashlib
# h = hashlib.md5(b'test').hexdigest()
'''
from Crypto.Cipher import DES
cipher = DES.new(key, DES.MODE_ECB)
'''
def normal_function():
    # rsa.generate_private_key(65537, 2048)
    return 42
"""
    findings = scan_python_code("test_repo", "test.py", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Expected 0 findings in comments, got: {crypto_findings}"


def test_java_commented_code_ignored():
    code = """
public class SafeService {
    // MessageDigest md = MessageDigest.getInstance("MD5");
    /*
     * Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");
     * KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
     */
    public int compute() {
        // String algo = "SHA-1";
        return 100;
    }
}
"""
    findings = scan_java_code("test_repo", "SafeService.java", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Expected 0 findings in Java comments, got: {crypto_findings}"


def test_go_commented_code_ignored():
    code = """
package main

// import "crypto/md5"
// import "crypto/des"

/*
func oldCrypto() {
    h := md5.New()
    c, _ := des.NewCipher([]byte("12345678"))
}
*/

func compute() int {
    // rsa.GenerateKey(rand.Reader, 2048)
    return 100
}
"""
    findings = scan_go_code("test_repo", "main.go", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Expected 0 findings in Go comments, got: {crypto_findings}"


# ============================================================================
# 2. String Literal & Incidental Keyword Tests
# ============================================================================

def test_python_string_literals_do_not_trigger():
    code = """
log_message = "Migrated from MD5 and SHA1 to post-quantum safe hashing in 2026."
doc_string = "Do not use DES or RSA-1024 in any new implementation."
error_notice = "Failed connection to https://crypto.example.com/api/v1"
ticker = "BTC/USDT"
"""
    findings = scan_python_code("test_repo", "strings.py", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"String literals triggered false findings: {crypto_findings}"


def test_java_string_literals_do_not_trigger():
    code = """
public class Logger {
    public static final String MIGRATION_NOTE = "We decommissioned DES and RSA-2048.";
    public void log(String msg) {
        String notice = "Algorithm MD5 is strictly prohibited.";
        System.out.println(notice);
    }
}
"""
    findings = scan_java_code("test_repo", "Logger.java", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Java string literals triggered false findings: {crypto_findings}"


def test_go_string_literals_do_not_trigger():
    code = """
package main

import "fmt"

func main() {
    msg := "System notice: md5 and sha1 are deprecated."
    url := "https://api.crypto-service.local/des/status"
    fmt.Println(msg, url)
}
"""
    findings = scan_go_code("test_repo", "strings.go", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Go string literals triggered false findings: {crypto_findings}"


# ============================================================================
# 3. Substring Variable & Identifier Collisions
# ============================================================================

def test_python_identifier_substrings():
    code = """
destination_path = "/var/spool/mail"
des_file_count = 14
sha_hash_directory = "/tmp/cache"
md5_checksum_str = "abcdef0123456789"
rsakey_string = "non_crypto_token"
"""
    findings = scan_python_code("test_repo", "identifiers.py", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Python identifier substrings triggered false findings: {crypto_findings}"


def test_java_identifier_substrings():
    code = """
public class Config {
    private String destinationHost = "10.0.0.1";
    private int descriptorId = 42;
    private String shaValue = "dummy";
}
"""
    findings = scan_java_code("test_repo", "Config.java", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Java identifier substrings triggered false findings: {crypto_findings}"


def test_go_identifier_substrings():
    code = """
package main

var (
    destinationIP = "192.168.1.1"
    description   = "Server config"
    sharedSecret  = "mock_token"
)
"""
    findings = scan_go_code("test_repo", "config.go", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 0, f"Go identifier substrings triggered false findings: {crypto_findings}"


# ============================================================================
# 4. Malformed Syntax Handling
# ============================================================================

def test_python_syntax_error_handles_gracefully():
    broken_code = """
def incomplete_function(
    x = 10
    if x > 5:
        # missing closing parenthesis, block colon, and syntax
"""
    # Scanner must catch SyntaxError and return empty list rather than crashing
    findings = scan_python_code("test_repo", "broken.py", broken_code)
    assert findings == []


def test_java_malformed_code_handles_gracefully():
    broken_code = """
public class Broken {{{{
    void invalid_syntax @@@ !!!
"""
    findings = scan_java_code("test_repo", "Broken.java", broken_code)
    assert isinstance(findings, list)


def test_go_malformed_code_handles_gracefully():
    broken_code = """
package 1234_broken
func {{ (( %%
"""
    findings = scan_go_code("test_repo", "broken.go", broken_code)
    assert isinstance(findings, list)


# ============================================================================
# 5. Empty and Whitespace Inputs
# ============================================================================

@pytest.mark.parametrize("empty_input", ["", "   ", "\n\n\n\t\t\t\n"])
def test_all_scanners_empty_input(empty_input):
    assert scan_python_code("repo", "empty.py", empty_input) == []
    assert scan_java_code("repo", "Empty.java", empty_input) == []
    assert scan_go_code("repo", "empty.go", empty_input) == []


# ============================================================================
# 6. Large Input Linear Scaling Check
# ============================================================================

def test_large_input_scaling():
    # 5,000 lines of typical non-crypto business logic
    large_lines = ["x = i * 2\ny = str(x) + '_id'\nprint(y)" for i in range(1500)]
    large_code = "\n".join(large_lines)

    findings = scan_python_code("repo", "large.py", large_code)
    assert findings == []


# ============================================================================
# 7. Code On Same Line As Block Comments (Positive Detection)
# ============================================================================

def test_java_code_after_inline_block_comment_detected():
    code = '/* header notice */ KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");'
    findings = scan_java_code("repo", "App.java", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 1
    assert crypto_findings[0].algorithm == "RSA"


def test_go_code_after_inline_block_comment_detected():
    code = '/* header notice */ key, _ := rsa.GenerateKey(rand.Reader, 2048)'
    findings = scan_go_code("repo", "app.go", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 1
    assert crypto_findings[0].algorithm == "rsa"


def test_java_code_on_multiline_comment_closing_line_detected():
    code = """/*
 * Multi-line license block
 */ KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
"""
    findings = scan_java_code("repo", "App.java", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 1
    assert crypto_findings[0].algorithm == "RSA"
    assert crypto_findings[0].line == 3


def test_go_code_on_multiline_comment_closing_line_detected():
    code = """/*
 * Multi-line license block
 */ key, _ := rsa.GenerateKey(rand.Reader, 2048)
"""
    findings = scan_go_code("repo", "app.go", code)
    crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_findings) == 1
    assert crypto_findings[0].algorithm == "rsa"
    assert crypto_findings[0].line == 3


def test_url_slashes_in_string_literals_do_not_break_scanner():
    java_code = 'String endpoint = "https://api.example.com/v1/auth"; // comment\nCipher c = Cipher.getInstance("AES");'
    findings = scan_java_code("repo", "App.java", java_code)
    crypto = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto) == 1
    assert crypto[0].algorithm == "AES"

    go_code = 'url := "https://api.example.com/v1/auth" // comment\nc, _ := aes.NewCipher(key)'
    findings_go = scan_go_code("repo", "app.go", go_code)
    crypto_go = [f for f in findings_go if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(crypto_go) == 1
    assert crypto_go[0].algorithm == "aes"

