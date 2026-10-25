import pytest
import os
import networkx as nx
from datetime import timedelta
from fastapi.testclient import TestClient
from src.main import app
from src.core.auth_storage import default_auth_storage, LEGACY_BENCHMARK_PROJECTS
from src.core.auth import (
    hash_password, 
    create_access_token, 
    get_secret_key, 
    is_production, 
    is_anonymous_allowed
)
from src.api.routes import project_cache
from src.core.storage import default_storage

client = TestClient(app)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_REPO_PATH = os.path.join(BACKEND_DIR, "dataset", "corpus", "python_itsdangerous")
if not os.path.exists(TEST_REPO_PATH):
    TEST_REPO_PATH = BACKEND_DIR

@pytest.fixture(autouse=True)
def clean_test_users(monkeypatch):
    # Ensure strict authentication mode for auth tests by default
    monkeypatch.delenv("AGILEGRAPH_ALLOW_ANONYMOUS", raising=False)
    monkeypatch.delenv("AGILEGRAPH_ENV", raising=False)
    
    with default_auth_storage._get_connection() as conn:
        conn.execute("DELETE FROM users WHERE username IN ('test_alice', 'test_bob', 'test_charlie')")
        conn.execute("DELETE FROM user_projects WHERE owner_username IN ('test_alice', 'test_bob', 'test_charlie')")
        conn.commit()
    project_cache.pop("alice_private_project", None)
    default_storage.delete_project("alice_private_project")
    default_auth_storage.delete_project_owner("alice_private_project")
    
    yield
    
    with default_auth_storage._get_connection() as conn:
        conn.execute("DELETE FROM users WHERE username IN ('test_alice', 'test_bob', 'test_charlie')")
        conn.execute("DELETE FROM user_projects WHERE owner_username IN ('test_alice', 'test_bob', 'test_charlie')")
        conn.commit()
    project_cache.pop("alice_private_project", None)
    default_storage.delete_project("alice_private_project")
    default_auth_storage.delete_project_owner("alice_private_project")


def test_registration_and_login_flow():
    # 1. Register Alice
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "test_alice",
        "email": "alice@example.com",
        "password": "Password123!"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "test_alice"
    assert data["user"]["email"] == "alice@example.com"
    token = data["access_token"]

    # 2. Duplicate username rejected with 409
    dup_res = client.post("/api/v1/auth/register", json={
        "username": "test_alice",
        "email": "another@example.com",
        "password": "Password123!"
    })
    assert dup_res.status_code == 409

    # 3. Duplicate email rejected with 409
    dup_email = client.post("/api/v1/auth/register", json={
        "username": "test_charlie",
        "email": "alice@example.com",
        "password": "Password123!"
    })
    assert dup_email.status_code == 409

    # 4. Password validation (short password < 6 rejected with 400)
    short_pw = client.post("/api/v1/auth/register", json={
        "username": "test_charlie",
        "email": "charlie@example.com",
        "password": "123"
    })
    assert short_pw.status_code in (400, 422)

    # 5. Password validation (bcrypt byte limit > 72 bytes rejected with 400)
    long_pw = client.post("/api/v1/auth/register", json={
        "username": "test_charlie",
        "email": "charlie@example.com",
        "password": "A" * 75
    })
    assert long_pw.status_code == 400
    assert "72 bytes" in long_pw.json()["detail"]

    # 6. Successful login
    login_res = client.post("/api/v1/auth/login", json={
        "username": "test_alice",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 7. Failed login with wrong password
    bad_login = client.post("/api/v1/auth/login", json={
        "username": "test_alice",
        "password": "WrongPassword"
    })
    assert bad_login.status_code == 401
    assert "Invalid username or password" in bad_login.json()["detail"]

    # 8. Access profile with token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "test_alice"

    # 9. Logout and token invalidation
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # 10. Access profile with revoked token returns 401
    revoked_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["detail"]


def test_missing_and_invalid_token_rejections():
    # 1. Missing Authorization header returns 401
    r_no_header = client.get("/api/v1/projects/demo_proj/graph")
    assert r_no_header.status_code == 401
    assert "Authentication required" in r_no_header.json()["detail"]

    # 2. Malformed scheme (e.g. Basic instead of Bearer) returns 401
    r_basic = client.get("/api/v1/projects/demo_proj/graph", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert r_basic.status_code == 401
    assert "Expected 'Bearer <token>'" in r_basic.json()["detail"]

    # 3. Empty Bearer token returns 401
    r_empty_bearer = client.get("/api/v1/projects/demo_proj/graph", headers={"Authorization": "Bearer   "})
    assert r_empty_bearer.status_code == 401

    # 4. Tampered / corrupt JWT token returns 401
    r_corrupt = client.get("/api/v1/projects/demo_proj/graph", headers={"Authorization": "Bearer not.a.valid.jwt.token"})
    assert r_corrupt.status_code == 401

    # 5. Expired token returns 401
    expired_token = create_access_token({"sub": "test_alice"}, expires_delta=timedelta(seconds=-60))
    r_expired = client.get("/api/v1/projects/demo_proj/graph", headers={"Authorization": f"Bearer {expired_token}"})
    assert r_expired.status_code == 401


def test_anonymous_access_and_production_safety(monkeypatch):
    # 1. Default without any env var: anonymous access is strictly disabled
    monkeypatch.delenv("AGILEGRAPH_ALLOW_ANONYMOUS", raising=False)
    monkeypatch.delenv("AGILEGRAPH_ENV", raising=False)
    assert not is_anonymous_allowed()
    res_default = client.get("/api/v1/projects/demo_proj/graph")
    assert res_default.status_code == 401

    # 2. When AGILEGRAPH_ALLOW_ANONYMOUS=1 in development: anonymous access works
    monkeypatch.setenv("AGILEGRAPH_ALLOW_ANONYMOUS", "1")
    assert is_anonymous_allowed()

    # 3. In production: AGILEGRAPH_ALLOW_ANONYMOUS=1 is STRICTLY IGNORED and disabled
    monkeypatch.setenv("AGILEGRAPH_ENV", "production")
    monkeypatch.setenv("AGILEGRAPH_ALLOW_ANONYMOUS", "1")
    assert not is_anonymous_allowed()
    res_prod = client.get("/api/v1/projects/demo_proj/graph")
    assert res_prod.status_code == 401

    # 4. Production JWT secret key enforcement
    # Default secret in production raises RuntimeError
    monkeypatch.delenv("AGILEGRAPH_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="AGILEGRAPH_SECRET_KEY.*strictly required in production"):
        get_secret_key()

    # Secret key shorter than 32 chars in production raises RuntimeError
    monkeypatch.setenv("AGILEGRAPH_SECRET_KEY", "short_secret_key")
    with pytest.raises(RuntimeError, match="must be at least 32 characters long"):
        get_secret_key()

    # Valid secret key >= 32 chars succeeds in production
    valid_key = "a" * 32
    monkeypatch.setenv("AGILEGRAPH_SECRET_KEY", valid_key)
    assert get_secret_key() == valid_key


def test_cross_user_isolation_read_write_scan_export_delete(monkeypatch):
    monkeypatch.delenv("AGILEGRAPH_ALLOW_ANONYMOUS", raising=False)
    
    # 1. Register Alice and Bob
    res_alice = client.post("/api/v1/auth/register", json={
        "username": "test_alice",
        "email": "alice@test.local",
        "password": "AliceSecretPassword123"
    })
    token_alice = res_alice.json()["access_token"]

    res_bob = client.post("/api/v1/auth/register", json={
        "username": "test_bob",
        "email": "bob@test.local",
        "password": "BobSecretPassword123"
    })
    token_bob = res_bob.json()["access_token"]

    # 2. Set up Alice's private project in cache and storage
    g = nx.MultiDiGraph()
    g.add_node("asset_1", type="CryptoUsageNode", category="crypto_usage", algorithm="RSA-2048", file="auth.py", line=42)
    scores = [{
        "asset_id": "asset_1",
        "score": 0.85,
        "classification": "HIGH",
        "missing_factors": [],
        "factors": {"migration_difficulty": {"value": 0.7}}
    }]
    scan_data = {
        "graph": g,
        "scores": scores,
        "provenance": {"scored_assets": 1, "unrated_assets": 0, "skipped_files": 0}
    }
    project_cache["alice_private_project"] = scan_data
    default_storage.save_scan_result("alice_private_project", scan_data)
    default_auth_storage.assign_project_owner("alice_private_project", "test_alice")

    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # 3. Cross-User READ attempts by Bob on Alice's project -> All return 403 Forbidden
    endpoints_to_test = [
        f"/api/v1/projects/alice_private_project/graph",
        f"/api/v1/projects/alice_private_project/risk",
        f"/api/v1/projects/alice_private_project/report/json",
        f"/api/v1/projects/alice_private_project/report/markdown",
        f"/api/v1/product/alice_private_project/pqc-readiness",
        f"/api/v1/product/alice_private_project/crypto-inventory",
        f"/api/v1/product/alice_private_project/assets/asset_1/priority",
        f"/api/v1/product/alice_private_project/assets/asset_1/roadmap",
    ]
    for ep in endpoints_to_test:
        r_bob = client.get(ep, headers=headers_bob)
        assert r_bob.status_code == 403, f"Endpoint {ep} should reject Bob with 403, got {r_bob.status_code}"
        assert "Access denied" in r_bob.json()["detail"]

    # 4. Cross-User WRITE / MUTATION attempts by Bob on Alice's project -> Return 403 Forbidden
    # A. Bob attempts to transition roadmap state on Alice's project
    r_bob_trans = client.post(
        "/api/v1/product/alice_private_project/assets/asset_1/roadmap",
        json={"requested_state": "EVALUATED"},
        headers=headers_bob
    )
    assert r_bob_trans.status_code == 403
    assert "Access denied" in r_bob_trans.json()["detail"]

    # B. Bob attempts to scan/overwrite Alice's project
    r_bob_scan = client.post(
        "/api/v1/scan",
        json={
            "repository_path": TEST_REPO_PATH,
            "project_id": "alice_private_project"
        },
        headers=headers_bob
    )
    assert r_bob_scan.status_code == 403
    assert "owned by another user" in r_bob_scan.json()["detail"]

    # C. Bob attempts to delete Alice's project
    r_bob_del = client.delete("/api/v1/projects/alice_private_project", headers=headers_bob)
    assert r_bob_del.status_code == 403
    assert "Access denied" in r_bob_del.json()["detail"]

    # 5. Alice (Owner) CAN access her own endpoints
    for ep in endpoints_to_test:
        r_alice = client.get(ep, headers=headers_alice)
        assert r_alice.status_code == 200, f"Endpoint {ep} should allow Alice, got {r_alice.status_code}"

    # Alice can transition roadmap state
    r_alice_trans = client.post(
        "/api/v1/product/alice_private_project/assets/asset_1/roadmap",
        json={"requested_state": "EVALUATED"},
        headers=headers_alice
    )
    assert r_alice_trans.status_code == 200
    assert r_alice_trans.json()["current_state"] == "EVALUATED"

    # Alice can delete her own project
    r_alice_del = client.delete("/api/v1/projects/alice_private_project", headers=headers_alice)
    assert r_alice_del.status_code == 200
    assert r_alice_del.json()["status"] == "success"


def test_unknown_and_legacy_project_ownership_policy(monkeypatch):
    monkeypatch.delenv("AGILEGRAPH_ALLOW_ANONYMOUS", raising=False)

    # Register Bob
    res_bob = client.post("/api/v1/auth/register", json={
        "username": "test_bob",
        "email": "bob@test.local",
        "password": "BobSecretPassword123"
    })
    token_bob = res_bob.json()["access_token"]
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # 1. Unknown / ownerless project that is NOT in benchmark whitelist:
    # Access MUST be denied (returns 403), never automatically accessible
    r_unknown = client.get("/api/v1/projects/unknown_orphan_project_xyz/graph", headers=headers_bob)
    assert r_unknown.status_code == 403
    assert "Access denied" in r_unknown.json()["detail"]

    # 2. Legacy benchmark projects and 'agile' are in whitelist
    assert "agile" in LEGACY_BENCHMARK_PROJECTS
    assert "python_cryptography" in LEGACY_BENCHMARK_PROJECTS

    # Authenticated researchers have read access to shared reference benchmark projects
    # (Checking ownership policy directly on auth_storage)
    assert default_auth_storage.check_user_owns_project("agile", "test_bob", write=False) is True
    assert default_auth_storage.check_user_owns_project("python_cryptography", "test_bob", write=False) is True

    # 3. Reading does NOT silently assign ownership to Bob
    assert default_auth_storage.get_project_owner("agile") is None
    assert default_auth_storage.get_project_owner("python_cryptography") is None

    # 4. Modifying / overwriting shared benchmark projects is rejected with write=True
    assert default_auth_storage.check_user_owns_project("agile", "test_bob", write=True) is False
    assert default_auth_storage.check_user_owns_project("python_cryptography", "test_bob", write=True) is False

    # Scanning over a shared benchmark project in authenticated mode is rejected with 403
    r_scan_shared = client.post(
        "/api/v1/scan",
        json={
            "repository_path": TEST_REPO_PATH,
            "project_id": "agile"
        },
        headers=headers_bob
    )
    assert r_scan_shared.status_code == 403
    assert "cannot overwrite shared research benchmark project" in r_scan_shared.json()["detail"]
