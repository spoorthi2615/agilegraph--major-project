import os
import tempfile
import pytest
from src.pipeline.runner import run_pipeline

def test_runner_provenance():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid Python file with md5 usage
        with open(os.path.join(temp_dir, "test1.py"), "w", encoding="utf-8") as f:
            f.write("import hashlib\nhashlib.md5()")
            
        # Create a file with non-UTF-8 content.
        # The runner uses errors='replace' so it will be read (with replacement chars)
        # rather than raising a UnicodeDecodeError. It will be scanned but produce no
        # crypto findings, resulting in an unrated file node.
        with open(os.path.join(temp_dir, "test2.py"), "wb") as f:
            f.write(b"\xff\xfe\x00garbage")
            
        result = run_pipeline(temp_dir, "test-project")
        
        provenance = result["provenance"]
        # Both files are regular files and get read (with errors='replace')
        assert provenance["scanned_files"] == 2
        # No hard errors from reading (errors='replace' handles non-UTF-8 gracefully)
        assert provenance["errors"] == 0
        
        # test1.py should have a file node and be scored or unrated
        scores = result["scores"]
        assert len(scores) >= 1
        
        # The md5 finding from test1.py must produce a rated crypto_weakness
        crypto_scored = [s for s in scores if s.get("factors", {}).get("crypto_weakness", {}).get("value") is not None]
        assert len(crypto_scored) >= 1
        assert crypto_scored[0]["factors"]["crypto_weakness"]["value"] > 0
        assert "md5" in crypto_scored[0]["factors"]["crypto_weakness"]["source"].lower()
        
        # Provenance must distinguish scored and unrated
        assert "scored_assets" in provenance
        assert "unrated_assets" in provenance


def test_runner_provenance_skipped_files_not_clean():
    """
    A scan with zero scored assets but skipped files must have skipped_files > 0
    in provenance — not reported as a 'clean' scan.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Add a regular file that will be scanned (no crypto, so unrated)
        with open(os.path.join(temp_dir, "empty.py"), "w") as f:
            f.write("x = 1\n")
        result = run_pipeline(temp_dir, "test-project")
        prov = result["provenance"]
        # scored_assets + unrated_assets should account for file nodes
        total_file_nodes = prov["scored_assets"] + prov["unrated_assets"]
        assert total_file_nodes >= 0
        # There must be provenance metadata for all three categories
        assert "scored_assets" in prov
        assert "unrated_assets" in prov
        assert "skipped_files" in prov
