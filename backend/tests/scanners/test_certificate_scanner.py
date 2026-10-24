import pytest
from src.scanners.certificates.scanner import scan_certificate_file, scan_certificate_in_code, parse_pem_certificate
from src.scanners.common.enums import AssetType, Language

# Real valid self-signed X.509 certificate generated for test fixture
SAMPLE_RSA_PEM = """-----BEGIN CERTIFICATE-----
MIICpjCCAY6gAwIBAgICA+gwDQYJKoZIhvcNAQELBQAwFjEUMBIGA1UEAwwLZXhh
bXBsZS5jb20wHhcNMjYxMDExMDgwNDMyWhcNMjcxMDExMDgwNDMyWjAWMRQwEgYD
VQQDDAtleGFtcGxlLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
ALaWeXkxp5aDlzpIp7DWG0p4Hl+EyujdmhLya4jxDWbAcZG75JyuI0mTx40OlblE
dxPmF/YH0fgGM9fdqUjqPDARtPMr5M2pRFK/atXHOFq4wz+i3AiLxU6CWQYfVXso
/kNLnfP6zazXikYdO647ErcjpMZaij7Sqt88k8ZfNJJ5r13dYgu+BYNIjAeAc9Qo
ZmsvlxE6ZYkyiRmisq5xpKCeAgwfu0rtAHQ4Kps3Vgmmry9DkyChwYSdIrPDUk6r
ucpsdfpA3QF+hQs6aZCfz9DCDMU9sLIhsi4z0b85cKoae9aph6+kzQI9FTRdFpxM
ydul1Ov9lWx4fIqsdnMGVY0CAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAUxXI8o0m
dia0Szuh8TLEFbmy+cb6Sy1D8rgZKlWApbdJY6fUR+xfIhxF8Sqs3qPTaFCjzT0A
ztno8f73VCQJ3e3nSCDyCksZSXIJFFod5mjKhX391xRT5AQhl7uAWnkhK8n/ZgiN
X8TOhbknM64qu8k45jzahQFZUMXHQHLsN069sBKRaAZby4q+RPNJp+XANWvwVS28
LIQtVLtoNd23RX2icV6MEPdSpdnL5ELKdfd27lPA1F5X8HAZkM4w+t53x7cKd0Au
lvhh2eiknLrSfbeYJDzqPIKM4iwY+YkCV5if7yfYdQ/hVwUR4DYn9qcTI7WQ+/4P
9MhZRGixjKn0FA==
-----END CERTIFICATE-----"""

def test_parse_pem_certificate():
    parsed = parse_pem_certificate(SAMPLE_RSA_PEM)
    assert parsed is not None
    assert parsed["algorithm"] == "rsa"
    assert parsed["key_size"] == 2048
    assert "example.com" in parsed["subject"]

def test_scan_certificate_file_detection():
    findings = scan_certificate_file("test-repo", "certs/server.crt", SAMPLE_RSA_PEM)
    assert len(findings) == 1
    f = findings[0]
    assert f.asset_type == AssetType.CERTIFICATE
    assert f.file == "certs/server.crt"
    assert f.confidence >= 0.85

def test_scan_certificate_file_raw_extension():
    findings = scan_certificate_file("test-repo", "ca.pem", "binary_data")
    assert len(findings) == 1
    assert findings[0].asset_type == AssetType.CERTIFICATE
    assert findings[0].file == "ca.pem"

def test_scan_certificate_in_python_code():
    code = """
import ssl
context = ssl.create_default_context(cafile="ca.pem")
context.load_cert_chain(certfile="server.crt")
"""
    findings = scan_certificate_in_code("test-repo", "tls_setup.py", code, Language.PYTHON)
    assert len(findings) >= 2
    apis = [f.api for f in findings if f.api]
    assert "ssl.create_default_context" in apis
    assert "load_cert_chain" in apis

def test_scan_certificate_in_java_code():
    code = """
import java.security.cert.CertificateFactory;
CertificateFactory cf = CertificateFactory.getInstance("X.509");
"""
    findings = scan_certificate_in_code("test-repo", "CertLoader.java", code, Language.JAVA)
    assert len(findings) >= 1
    assert any("CertificateFactory" in f.evidence for f in findings)

def test_scan_certificate_in_go_code():
    code = """
import "crypto/tls"
cert, err := tls.LoadX509KeyPair("server.crt", "server.key")
"""
    findings = scan_certificate_in_code("test-repo", "server.go", code, Language.GO)
    assert len(findings) >= 1
    assert any("tls.LoadX509KeyPair" in f.evidence for f in findings)
