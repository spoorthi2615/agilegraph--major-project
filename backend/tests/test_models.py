from src.models.nodes import FileNode, CryptoUsageNode, CertificateNode

def test_file_node():
    node = FileNode(id="f1", path="/src/Main.java", language="Java")
    assert node.path == "/src/Main.java"
    assert node.language == "Java"
    assert node.risk_score is None

def test_crypto_usage_node():
    node = CryptoUsageNode(id="c1", algorithm="RSA", strength=2048, risk_score=8.5)
    assert node.algorithm == "RSA"
    assert node.risk_score == 8.5

def test_certificate_node():
    node = CertificateNode(id="cert1", issuer="Let's Encrypt", expiry="2027-01-01")
    assert node.is_expired is False
