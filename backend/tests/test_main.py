from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to AgileGraph API"}

def test_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "AgileGraph backend is running."}

def test_mosca_index():
    response = client.get("/api/v1/mosca-index?confidentiality=10&migration=5&quantum=20")
    assert response.status_code == 200
    assert response.json()["readiness"] == "Safe"
    
    response2 = client.get("/api/v1/mosca-index?confidentiality=10&migration=15&quantum=20")
    assert response2.json()["readiness"] == "Vulnerable"
