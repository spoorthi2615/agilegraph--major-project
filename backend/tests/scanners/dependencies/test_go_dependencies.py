from src.scanners.dependencies.scanner import scan_manifest

def test_parse_go_mod():
    content = """module example.com/app
    
require (
    golang.org/x/crypto v0.0.0-20210921155107-089bfa567519
    github.com/google/uuid v1.3.0 // indirect
)
require example.com/other v1.0.0
"""
    records = scan_manifest("repo", "go.mod", content)
    assert len(records) == 3
    
    crypto = [r for r in records if r.package_name == "golang.org/x/crypto"][0]
    assert crypto.crypto_relevance == "CRYPTOGRAPHIC"
    assert crypto.direct is True
    
    indirect = [r for r in records if r.package_name == "github.com/google/uuid"][0]
    assert indirect.direct is False
