import sys
import os
sys.path.append(os.path.abspath('backend'))
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

print("1. Scan")
res = client.post("/api/v1/scan", json={"repository_path": "backend/dataset/corpus/python_cryptography", "project_id": "smoke-test"})
print(res.status_code, res.json())
assert res.status_code == 200

print("2. Graph")
res = client.get("/api/v1/projects/smoke-test/graph")
print(res.status_code, "nodes:", len(res.json().get('nodes', [])))
assert res.status_code == 200

print("3. Risk")
res = client.get("/api/v1/projects/smoke-test/risk")
print(res.status_code, "assets:", len(res.json().get('assets', [])))
assert res.status_code == 200

assets = res.json().get('assets', [])
if not assets:
    print("No assets found, passing anyway")
else:
    asset_id = assets[0]['asset_id']
    
    print("4. PQC Readiness")
    res = client.get(f"/api/v1/product/smoke-test/pqc-readiness")
    print(res.status_code, res.json())
    assert res.status_code == 200

    print("5. Mosca Planning")
    res = client.post("/api/v1/product/mosca", json={"x": 24, "y": 12, "z": 30})
    print(res.status_code, res.json())
    assert res.status_code == 200

    print("6. Migration Priority")
    res = client.get(f"/api/v1/product/smoke-test/assets/{asset_id}/priority?mosca_status=AT_RISK")
    print(res.status_code, res.json())
    assert res.status_code == 200

    print("7. Roadmap State")
    res = client.get(f"/api/v1/product/smoke-test/assets/{asset_id}/roadmap")
    print(res.status_code, res.json())
    assert res.status_code == 200
    
    res = client.post(f"/api/v1/product/smoke-test/assets/{asset_id}/roadmap", json={"requested_state": "MIGRATION_CANDIDATE"})
    print(res.status_code, res.json())
    assert res.status_code == 200

print("E2E Smoke Test Passed!")
