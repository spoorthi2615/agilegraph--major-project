import os
import tempfile
import pytest
from src.pipeline.runner import run_pipeline

def test_runner_provenance():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid Python file
        with open(os.path.join(temp_dir, "test1.py"), "w", encoding="utf-8") as f:
            f.write("import hashlib\nhashlib.md5()")
            
        # Create a file that will raise a parsing error (SyntaxError is caught in scanner but we want to simulate an unreadable file or something)
        # Actually, let's create a file with invalid encoding so `content = f.read()` raises UnicodeDecodeError
        with open(os.path.join(temp_dir, "test2.py"), "wb") as f:
            f.write(b"\xff\xfe\x00")
            
        result = run_pipeline(temp_dir, "test-project")
        
        provenance = result["provenance"]
        assert provenance["scanned_files"] == 2
        assert provenance["errors"] == 1
        assert "test2.py" in provenance["error_details"][0]["file"]
        
        # Check that test1.py's finding was recorded and resulted in a score with MD5
        scores = result["scores"]
        assert len(scores) == 1
        assert "md5" in scores[0]["factors"]["crypto_weakness"]["source"].lower()
        assert scores[0]["factors"]["crypto_weakness"]["value"] > 0
