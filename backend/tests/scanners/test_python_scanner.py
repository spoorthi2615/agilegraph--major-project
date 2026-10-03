from src.scanners.python.scanner import scan_python_code
from src.scanners.common.enums import AssetType

def test_scan_python_imports():
    code = "import cryptography\nimport hashlib\nimport os"
    findings = scan_python_code("repo", "main.py", code)
    
    assert len(findings) == 2
    assert findings[0].asset_type == AssetType.LIBRARY
    assert findings[0].library in ["cryptography", "hashlib"]
    assert findings[1].library in ["cryptography", "hashlib"]
    assert findings[0].file == "main.py"

def test_scan_python_calls():
    code = "import hashlib\nm = hashlib.md5()"
    findings = scan_python_code("repo", "main.py", code)
    
    calls = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(calls) == 1
    assert calls[0].api == "hashlib.md5"
    assert calls[0].algorithm == "md5"
    assert calls[0].line == 2
