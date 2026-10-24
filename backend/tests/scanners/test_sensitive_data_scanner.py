import pytest
from src.scanners.sensitive_data.scanner import scan_sensitive_data, classify_identifier
from src.scanners.common.enums import AssetType, Language

def test_classify_identifier():
    assert classify_identifier("user_password")[1] == "CRITICAL"
    assert classify_identifier("rsa_private_key")[1] == "CRITICAL"
    assert classify_identifier("stripe_api_key")[1] == "HIGH"
    assert classify_identifier("credit_card_number")[1] == "HIGH"
    assert classify_identifier("user_session_id")[1] == "MEDIUM"
    assert classify_identifier("counter")[1] == "LOW"

def test_scan_python_sensitive_variables():
    code = """
import os

password = os.environ.get("DB_PASSWORD")
admin_private_key: str = load_key()
api_key = "secret_123"
session_id = "sess_456"
# this is a comment about password that should be ignored
counter = 42
"""
    findings = scan_sensitive_data("repo", "config.py", code, Language.PYTHON)
    assert len(findings) >= 4
    names = [f.extra.get("name").lower() for f in findings]
    assert any("password" in n for n in names)
    assert any("private_key" in n for n in names)
    assert any("api_key" in n for n in names)
    assert any("session_id" in n for n in names)
    assert not any("counter" in n for n in names)

    classifications = {f.extra.get("name"): f.extra.get("classification") for f in findings}
    assert any(c == "CRITICAL" for c in classifications.values())
    assert any(c == "HIGH" for c in classifications.values())
    assert any(c == "MEDIUM" for c in classifications.values())

def test_scan_java_sensitive_fields():
    code = """
public class UserCredentials {
    private String password;
    private byte[] privateKey;
    public String apiKey;
    private int loginAttempts;
}
"""
    findings = scan_sensitive_data("repo", "UserCredentials.java", code, Language.JAVA)
    assert len(findings) >= 3
    names = [f.extra.get("name").lower() for f in findings]
    assert any("password" in n for n in names)
    assert any("privatekey" in n for n in names)
    assert any("apikey" in n for n in names)
    assert not any("loginattempts" in n for n in names)

def test_scan_go_sensitive_struct():
    code = """
package models

type AuthConfig struct {
    Password string
    PrivateKey []byte
    ApiKey string
    Port int
}
"""
    findings = scan_sensitive_data("repo", "auth.go", code, Language.GO)
    assert len(findings) >= 3
    names = [f.extra.get("name").lower() for f in findings]
    assert any("password" in n for n in names)
    assert any("privatekey" in n for n in names)
    assert any("apikey" in n for n in names)
    assert not any("port" in n for n in names)

def test_scan_sensitive_data_negative():
    code = """
def add(x, y):
    result = x + y
    return result
"""
    findings = scan_sensitive_data("repo", "utils.py", code, Language.PYTHON)
    assert len(findings) == 0
