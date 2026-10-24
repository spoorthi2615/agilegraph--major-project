import sys
import os
sys.path.append(os.path.abspath('backend'))
from fastapi.testclient import TestClient
from src.main import app
import json

client = TestClient(app)

print("Scanning...")
client.post("/api/v1/scan", json={"repository_path": "backend/dataset/corpus/python_cryptography", "project_id": "test-inventory"})

print("Fetching Inventory...")
res = client.get("/api/v1/product/test-inventory/crypto-inventory")
print(res.status_code)
print(json.dumps(res.json(), indent=2)[:500])
