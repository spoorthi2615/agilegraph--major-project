import pytest
import os
import tempfile
import json
import subprocess
import sys

def test_cli_scan_valid():
    with tempfile.TemporaryDirectory() as temp_repo, tempfile.TemporaryDirectory() as temp_out:
        # Create a test python file
        with open(os.path.join(temp_repo, "main.py"), "w") as f:
            f.write("import hashlib\nm = hashlib.md5()\n")
            
        output_file = os.path.join(temp_out, "report.json")
        
        # Run CLI
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env["AGILEGRAPH_SCAN_ROOT"] = temp_repo
        
        cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
        
        result = subprocess.run(
            [sys.executable, cli_path, "scan", temp_repo, "--output", output_file, "--project-id", "test-project"],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed with error: {result.stderr}"
        assert os.path.exists(output_file)
        
        with open(output_file, "r") as f:
            data = json.load(f)
            
        assert data["project_id"] == "test-project"
        assert data["analysis_type"] == "HEURISTIC"
        assert data["ml_status"] == "BLOCKED"
        assert data["expert_validation_status"] == "BLOCKED"
        assert data["missing_data_policy"] == "RENORMALIZE"
        assert "provenance" in data
        assert data["provenance"]["scanned_files"] > 0
        assert len(data["assets"]) > 0
        assert "graph" in data
        assert len(data["graph"]["nodes"]) > 0
        
        # Check heuristic constraints
        asset = data["assets"][0]
        assert "factors" in asset
        assert "weights" in asset
        assert "missing_factors" in asset

def test_cli_scan_invalid_repo():
    with tempfile.TemporaryDirectory() as temp_out:
        output_file = os.path.join(temp_out, "report.json")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
        
        result = subprocess.run(
            [sys.executable, cli_path, "scan", "/does/not/exist/repo", "--output", output_file],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "Repository path does not exist" in result.stderr

def test_cli_scan_missing_args():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
    
    result = subprocess.run(
        [sys.executable, cli_path, "scan", "."],
        env=env,
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "required" in result.stderr
