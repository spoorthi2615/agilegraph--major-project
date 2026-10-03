import os
import tempfile
import pytest
from src.pipeline.runner import run_pipeline

def test_runner_filesystem_protections():
    with tempfile.TemporaryDirectory() as root:
        allowed = os.path.join(root, "allowed")
        os.makedirs(allowed)
        
        # 1. Legitimate repository inside allowed
        repo = os.path.join(allowed, "repo")
        os.makedirs(repo)
        
        # Create a file inside repo
        safe_file = os.path.join(repo, "safe.py")
        with open(safe_file, "w") as f:
            f.write("import hashlib\nhashlib.md5()")
            
        # 2. Outside root target (sibling-prefix)
        sibling = os.path.join(root, "allowed_sibling")
        os.makedirs(sibling)
        
        # 3. File symlink pointing outside allowed root but located inside repo
        secret = os.path.join(root, "secret.py")
        with open(secret, "w") as f:
            f.write("import hashlib\nhashlib.md5()")
            
        symlink = os.path.join(repo, "leak.py")
        try:
            os.symlink(secret, symlink)
        except OSError:
            # On Windows without developer mode, symlinks might fail
            pass
            
        # Test 1: Sibling path
        with pytest.raises(ValueError, match="outside allowed scan root"):
            run_pipeline(sibling, "test", allowed_root=allowed)
            
        # Test 2: .. path escape
        escape = os.path.join(allowed, "..", "allowed_sibling")
        with pytest.raises(ValueError, match="outside allowed scan root"):
            run_pipeline(escape, "test", allowed_root=allowed)
            
        # Test 3: directory symlink escape
        dir_sym = os.path.join(root, "dir_sym")
        try:
            os.symlink(sibling, dir_sym)
            with pytest.raises(ValueError, match="outside allowed scan root"):
                run_pipeline(dir_sym, "test", allowed_root=allowed)
        except OSError:
            pass
            
        # Test 4: legit repo works, and canonical path is passed
        res = run_pipeline(repo, "test", allowed_root=allowed)
        assert res["provenance"]["scanned_files"] >= 1
        
        # If symlink was created, verify the secret file was not scanned (error recorded)
        if os.path.exists(symlink):
            assert len(res["provenance"]["error_details"]) == 1
            assert "Symlink escape" in res["provenance"]["error_details"][0]["error"]
