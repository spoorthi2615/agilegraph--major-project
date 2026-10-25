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

def test_scan_invalid_path(monkeypatch):
    import os
    # Mock the environment variable to a specific root
    monkeypatch.setenv("AGILEGRAPH_SCAN_ROOT", "/allowed/root")
    
    # Mock os.path.exists to always return True for tests
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    # Mock realpath to simulate symlink escapes
    original_realpath = os.path.realpath
    def mock_realpath(path):
        if path == "/allowed/root":
            return "/allowed/root"
        if "symlink_escape" in path:
            return "/etc/shadow" # simulates resolving to outside
        if path.startswith("/allowed/root"):
            return path
        return original_realpath(path)
        
    monkeypatch.setattr(os.path, "realpath", mock_realpath)
    
    # Symlink escape
    response = client.post("/api/v1/scan", json={"repository_path": "/allowed/root/symlink_escape", "project_id": "test"})
    assert response.status_code == 403
    
    # Outside paths
    for p in ["/etc", "/root", "/proc", "/boot", "/bin", "c:\\windows", ".."]:
        response = client.post("/api/v1/scan", json={"repository_path": p, "project_id": "test"})
        assert response.status_code == 403

def test_scan_legitimate_path(monkeypatch):
    import os
    # Allow scanning /var/www if the tool is configured to run from /var/www
    allowed = os.path.normpath("/var/www")
    repo = os.path.normpath("/var/www/myrepo")
    
    monkeypatch.setenv("AGILEGRAPH_SCAN_ROOT", allowed)
    orig_exists = os.path.exists
    monkeypatch.setattr(os.path, "exists", lambda p: True if p in (repo, allowed) else orig_exists(p))
    
    # Let realpath just return the normpath'd inputs directly
    monkeypatch.setattr(os.path, "realpath", lambda x: os.path.normpath(x))
    
    from src.core.storage import default_storage
    from src.core.auth_storage import default_auth_storage
    proj_id = "test_legit_scan_validation"
    try:
        # This shouldn't throw 403, as long as it's not 403, the security check passed.
        response = client.post("/api/v1/scan", json={"repository_path": repo, "project_id": proj_id})
        assert response.status_code != 403
    finally:
        default_storage.delete_project(proj_id)
        default_auth_storage.delete_project_owner(proj_id)
