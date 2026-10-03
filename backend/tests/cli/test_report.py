import pytest
import os
import tempfile
import json
import subprocess
import sys

def create_mock_json(path):
    data = {
        "project_id": "test",
        "analysis_type": "HEURISTIC",
        "ml_status": "BLOCKED",
        "expert_validation_status": "BLOCKED",
        "missing_data_policy": "RENORMALIZE",
        "provenance": {"scanned_files": 1},
        "assets": [{
            "asset_id": "test.py",
            "score": 0.5,
            "factors": {},
            "weights": {},
            "weighted_contributions": {},
            "missing_factors": ["cve_risk"]
        }],
        "graph": {"nodes": [], "edges": []}
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path

def test_cli_report_valid():
    with tempfile.TemporaryDirectory() as temp_dir:
        json_path = os.path.join(temp_dir, "scan.json")
        create_mock_json(json_path)
        
        md_path = os.path.join(temp_dir, "report.md")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
        
        result = subprocess.run(
            [sys.executable, cli_path, "report", json_path, "--output", md_path],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert os.path.exists(md_path)
        
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        assert "HEURISTIC ANALYSIS" in content
        assert "GATv2**: `PENDING_EXPERT_LABELS`" in content
        assert "Expert validation**: `BLOCKED`" in content
        assert "Empirical evaluation**: `BLOCKED`" in content
        assert "No fabricated empirical metrics" in content
        assert "cve_risk" in content

def test_cli_report_invalid_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        json_path = os.path.join(temp_dir, "scan.json")
        with open(json_path, "w") as f:
            f.write("not valid json")
            
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
        
        result = subprocess.run(
            [sys.executable, cli_path, "report", json_path],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0

def test_cli_report_missing_fields():
    with tempfile.TemporaryDirectory() as temp_dir:
        json_path = os.path.join(temp_dir, "scan.json")
        with open(json_path, "w") as f:
            json.dump({"project_id": "test"}, f)
            
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cli_path = os.path.join(env["PYTHONPATH"], "src", "cli.py")
        
        result = subprocess.run(
            [sys.executable, cli_path, "report", json_path],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "Missing required field" in result.stderr
