from src.scanners.go.scanner import scan_go_code
from src.scanners.common.enums import AssetType

def test_go_scanner_rsa():
    code = 'import "crypto/rsa"\nkey, err := rsa.GenerateKey(rand.Reader, 2048)'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "rsa"
    assert usage.operation == "key_generation"

def test_go_scanner_rsa_sign_and_encrypt():
    code = (
        'import "crypto/rsa"\n'
        'sig, err := rsa.SignPSS(rand.Reader, priv, crypto.SHA256, hashed, nil)\n'
        'ct, err2 := rsa.EncryptOAEP(sha256.New(), rand.Reader, &priv.PublicKey, msg, label)'
    )
    findings = scan_go_code("repo", "main.go", code)
    usages = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(usages) == 2
    assert usages[0].operation == "signature"
    assert usages[1].operation == "encryption"

def test_go_scanner_ecdsa():
    code = 'import "crypto/ecdsa"\nkey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)'
    findings = scan_go_code("repo", "main.go", code)
    assert len(findings) == 2
    usage = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE][0]
    assert usage.algorithm == "ecdsa"

def test_go_scanner_ed25519_and_elliptic():
    code = (
        'import "crypto/ed25519"\n'
        'import "crypto/elliptic"\n'
        'pub, priv, err := ed25519.GenerateKey(rand.Reader)\n'
        'curve := elliptic.P256()'
    )
    findings = scan_go_code("repo", "main.go", code)
    usages = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(usages) == 2
    assert any(u.algorithm == "ed25519" and u.operation == "key_generation" for u in usages)
    assert any(u.algorithm == "elliptic" and u.operation == "elliptic_curve" for u in usages)

def test_go_scanner_tls():
    code = 'import "crypto/tls"\ncfg := &tls.Config{MinVersion: tls.VersionTLS13}'
    findings = scan_go_code("repo", "main.go", code)
    usages = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
    assert len(usages) >= 1
    assert usages[0].algorithm == "tls"
    assert usages[0].operation == "tls_config"

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
