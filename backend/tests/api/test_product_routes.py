import pytest
from fastapi.testclient import TestClient
import networkx as nx

from src.main import app
from src.api.routes import project_cache
from src.api.product_routes import roadmap_state_store
from src.models.migration_state import RoadmapState

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_mock_project():
    # Setup a mock graph and scores for testing product routes without running a real scan
    g = nx.MultiDiGraph()
    g.add_node("asset_1", type="CryptoUsageNode", algorithm="rsa")
    g.add_node("asset_2", type="CryptoUsageNode", algorithm="unknown")
    g.add_node("asset_3", type="FileNode")

    scores = [
        {
            "asset_id": "asset_1",
            "score": 0.8,
            "missing_factors": [],
            "factors": {"migration_difficulty": {"value": 0.9}}
        },
        {
            "asset_id": "asset_2",
            "score": None,
            "missing_factors": ["data_sensitivity"]
        },
        {
            "asset_id": "asset_3",
            "score": 0.2,
            "missing_factors": []
        }
    ]

    project_cache["test_proj"] = {
        "graph": g,
        "scores": scores
    }
    
    roadmap_state_store.clear()
    
    yield
    
    project_cache.clear()
    roadmap_state_store.clear()


def test_pqc_readiness_endpoint():
    response = client.get("/api/v1/product/test_proj/pqc-readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_count"] == 3
    assert data["assessed_assets"] == 2
    assert data["insufficient_evidence_assets"] == 1
    assert data["migration_candidates"] == 1 # asset_1 has score 0.8 >= 0.5
    assert "rsa" in data["recognized_algorithms"]
    assert data["unknown_algorithms"] == 1
    assert "Preliminary heuristic" in data["status"]

def test_mosca_endpoint():
    response = client.post("/api/v1/product/mosca", json={"x": 24, "y": 12, "z": 30})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AT_RISK"
    assert data["total"] == 36

def test_mosca_endpoint_insufficient():
    response = client.post("/api/v1/product/mosca", json={"x": -1, "y": 12, "z": 30})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INSUFFICIENT_DATA"
    
def test_migration_priority_endpoint():
    # asset_1: risk 0.8, AT_RISK mosca -> HIGH
    response = client.get("/api/v1/product/test_proj/assets/asset_1/priority?mosca_status=AT_RISK")
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "HIGH"
    assert data["risk_score"] == 0.8
    assert data["mosca_status"] == "AT_RISK"
    assert data["pqc_relevance"] is True
    assert data["migration_difficulty"] == 0.9

def test_migration_priority_invalid_mosca():
    response = client.get("/api/v1/product/test_proj/assets/asset_1/priority?mosca_status=INVALID")
    assert response.status_code == 400

def test_migration_priority_not_assessed():
    response = client.get("/api/v1/product/test_proj/assets/asset_2/priority")
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "NOT_ASSESSED"
    assert data["risk_score"] is None
    
def test_roadmap_endpoint():
    # Initial state
    response = client.get("/api/v1/product/test_proj/assets/asset_1/roadmap")
    assert response.status_code == 200
    assert response.json()["current_state"] == "NOT_ASSESSED"
    
    # Valid transition
    response = client.post("/api/v1/product/test_proj/assets/asset_1/roadmap", json={"requested_state": "ASSESSMENT_REQUIRED"})
    assert response.status_code == 200
    assert response.json()["current_state"] == "ASSESSMENT_REQUIRED"
    
    # Invalid transition (jump)
    response = client.post("/api/v1/product/test_proj/assets/asset_1/roadmap", json={"requested_state": "VERIFIED"})
    assert response.status_code == 400
    assert "Invalid state transition" in response.json()["detail"]

def test_product_routes_missing_project():
    response = client.get("/api/v1/product/unknown_proj/pqc-readiness")
    assert response.status_code == 404

def test_product_routes_missing_asset():
    response = client.get("/api/v1/product/test_proj/assets/unknown_asset/priority")
    assert response.status_code == 404

def test_scan_backward_compatibility():
    # Ensure existing /scan endpoint is untouched and structurally sound (using /status)
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

import os
import tempfile

def test_actual_scan_backward_compatibility(monkeypatch):
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setenv("AGILEGRAPH_SCAN_ROOT", temp_dir)
        with open(os.path.join(temp_dir, "main.py"), "w") as f:
            f.write("import hashlib\nm = hashlib.md5()\n")
            
        scan_res = client.post("/api/v1/scan", json={
            "repository_path": temp_dir,
            "project_id": "test_proj_scan_compat"
        })
        assert scan_res.status_code == 200
        assert scan_res.json()["status"] == "success"
        
        # Verify response structure remains compatible
        data = scan_res.json()
        assert "asset_count" in data
        assert "scored_assets" in data

def test_product_endpoints_do_not_mutate_risk_or_graph():
    original_score = project_cache["test_proj"]["scores"][0]["score"]
    assert original_score == 0.8
    
    # 1. Changing Mosca Status does not alter risk
    client.get("/api/v1/product/test_proj/assets/asset_1/priority?mosca_status=AT_RISK")
    assert project_cache["test_proj"]["scores"][0]["score"] == 0.8
    
    # 2. Changing roadmap state does not alter risk
    client.post("/api/v1/product/test_proj/assets/asset_1/roadmap", json={"requested_state": "ASSESSMENT_REQUIRED"})
    assert project_cache["test_proj"]["scores"][0]["score"] == 0.8
    
    # Check graph remains unmodified
    g = project_cache["test_proj"]["graph"]
    assert len(g.nodes) == 3

def test_insufficient_data_serialization():
    # Asset 2 has None risk score
    response = client.get("/api/v1/product/test_proj/assets/asset_2/priority")
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == "NOT_ASSESSED"
    assert data["risk_score"] is None
    assert "mosca_status is a provided planning input" in data["mosca_provenance"]
