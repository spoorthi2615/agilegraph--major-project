from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.dependencies.scanner import scan_manifest
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.graph.validation import validate_graph

def test_integration_pipeline():
    python_code = "import hashlib\nm = hashlib.md5()"
    java_code = 'import javax.crypto.Cipher;\nCipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");'
    go_code = 'import "crypto/aes"\nblock, err := aes.NewCipher(key)'
    
    # 1. Scan
    py_findings = scan_python_code("synthetic", "main.py", python_code)
    java_findings = scan_java_code("synthetic", "Main.java", java_code)
    go_findings = scan_go_code("synthetic", "main.go", go_code)
    
    # 1.5 Scan Dependencies
    reqs_content = "hashlib\njavax.crypto.Cipher\n"
    dep_findings_py = scan_manifest("synthetic", "requirements.txt", reqs_content)
    
    go_mod_content = "module test\nrequire crypto/aes v1.0.0\n"
    dep_findings_go = scan_manifest("synthetic", "go.mod", go_mod_content)
    
    all_findings = py_findings + java_findings + go_findings + dep_findings_py + dep_findings_go
    
    # 2. Build Graph
    ag = AgileGraph()
    builder = GraphBuilder(ag)
    builder.build_from_normalized_records(all_findings)
    
    # 3. Verify Graph Content
    assert ag.get_node("synthetic:main.py") is not None
    assert ag.get_node("synthetic:Main.java") is not None
    assert ag.get_node("synthetic:main.go") is not None
    
    # Check library nodes
    assert ag.get_node("synthetic:library:hashlib") is not None
    assert ag.get_node("synthetic:library:javax.crypto.Cipher") is not None
    
    # Check enriched property
    aes_lib = ag.get_node("synthetic:library:crypto/aes")
    assert aes_lib is not None
    assert aes_lib.properties.get("manifest_file") == "go.mod"
    
    # 4. Validate graph
    errors = validate_graph(ag)
    assert len(errors) == 0
