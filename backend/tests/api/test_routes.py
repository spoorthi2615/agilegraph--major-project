import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_api_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_scan_nonexistent_repo():
    response = client.post("/api/v1/scan", json={
        "repository_path": "/path/does/not/exist",
        "project_id": "test_proj"
    })
    assert response.status_code == 400

def test_scan_and_fetch(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("AGILEGRAPH_SCAN_ROOT", temp_dir)
        # Create a test python file so the scanner finds a node
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write("import hashlib\nm = hashlib.md5()\n")
            
        # Trigger scan
        scan_res = client.post("/api/v1/scan", json={
            "repository_path": temp_dir,
            "project_id": "test_proj_2"
        })
        assert scan_res.status_code == 200
        assert scan_res.json()["status"] == "success"
        
        # Fetch graph
        graph_res = client.get("/api/v1/projects/test_proj_2/graph")
        assert graph_res.status_code == 200
        graph_data = graph_res.json()
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["edges"]) > 0
        
        # Fetch risk
        risk_res = client.get("/api/v1/projects/test_proj_2/risk")
        assert risk_res.status_code == 200
        risk_data = risk_res.json()
        assert len(risk_data["assets"]) > 0
        assert risk_data["ml_status"] == "BLOCKED"
        assert risk_data["expert_validation_status"] == "BLOCKED"

def test_fetch_missing_project():
    res1 = client.get("/api/v1/projects/missing/graph")
    assert res1.status_code == 404
    
    res2 = client.get("/api/v1/projects/missing/risk")
    assert res2.status_code == 404
