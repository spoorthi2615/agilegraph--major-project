import pytest
from src.scanners.tls.scanner import scan_tls_endpoint

def test_tls_scanner_authorized():
    findings = scan_tls_endpoint("127.0.0.1", 443, authorized=True)
    assert len(findings) == 1
    assert findings[0].extra["host"] == "127.0.0.1"

def test_tls_scanner_unauthorized():
    with pytest.raises(PermissionError, match="requires the --authorized flag"):
        scan_tls_endpoint("example.com", 443, authorized=False)
