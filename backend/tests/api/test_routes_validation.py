import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_mosca_index_valid():
    response = client.get("/api/v1/mosca-index?confidentiality=10&migration=5&quantum=20")
    assert response.status_code == 200
    assert response.json()["readiness"] == "Safe"

def test_mosca_index_invalid():
    response = client.get("/api/v1/mosca-index?confidentiality=-1")
    assert response.status_code == 400
    assert "non-negative" in response.json()["detail"].lower()

def test_scan_invalid_path():
    # Trying to scan a system directory
    response = client.post("/api/v1/scan", json={"repository_path": "c:\\windows", "project_id": "test"})
    # Windows system roots may exist, so it should trigger 403. If not existing (Linux machine running test for c:\windows), it triggers 400.
    assert response.status_code in (400, 403)
    
    response = client.post("/api/v1/scan", json={"repository_path": "/etc", "project_id": "test"})
    assert response.status_code in (400, 403)
