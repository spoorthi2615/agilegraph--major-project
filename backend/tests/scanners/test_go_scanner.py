from src.scanners.go.scanner import scan_go_code
from src.scanners.common.enums import AssetType

def test_go_scanner_rsa():
    code = 'import "crypto/rsa"\nkey, err := rsa.GenerateKey(rand.Reader, 2048)'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "rsa"
    assert usage.operation == "key_generation"

def test_go_scanner_ecdsa():
    code = 'import "crypto/ecdsa"\nkey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "ecdsa"

def test_go_scanner_aes():
    code = 'import "crypto/aes"\nblock, err := aes.NewCipher(key)'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "aes"
    assert usage.operation == "encryption"

def test_go_scanner_sha():
    code = 'import "crypto/sha256"\nh := sha256.New()'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "sha256"
    assert usage.operation == "hashing"

def test_go_scanner_unrelated():
    code = 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello") }'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 0

def test_go_scanner_malformed():
    code = 'just some text with no crypto imports'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 0
