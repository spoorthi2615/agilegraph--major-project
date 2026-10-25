import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.migration_state import MigrationLifecycleState

client = TestClient(app)

CORPUS_TARGET = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "corpus", "python_cryptography")
)


@pytest.mark.skipif(not os.path.exists(CORPUS_TARGET), reason="Benchmark corpus target not found on disk")
def test_e2e_pipeline_smoke():
    """
    End-to-end smoke test validating pipeline execution across scanning,
    graph retrieval, risk evaluation, crypto-inventory, Mosca, and roadmap lifecycle endpoints.
    """
    proj_id = "e2e-smoke-test-project"

    # 1. Trigger scan
    scan_res = client.post(
        "/api/v1/scan",
        json={"repository_path": CORPUS_TARGET, "project_id": proj_id}
    )
    assert scan_res.status_code == 200, f"Scan failed: {scan_res.text}"
    scan_data = scan_res.json()
    assert scan_data.get("project_id") == proj_id

    # 2. Graph retrieval
    graph_res = client.get(f"/api/v1/projects/{proj_id}/graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert len(graph_data.get("nodes", [])) > 0

    # 3. Risk scoring
    risk_res = client.get(f"/api/v1/projects/{proj_id}/risk")
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assets = risk_data.get("assets", [])
    assert len(assets) > 0

    # 4. Crypto inventory
    inv_res = client.get(f"/api/v1/product/{proj_id}/crypto-inventory")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert len(inv_data.get("items", [])) > 0

    # 5. PQC readiness summary
    pqc_res = client.get(f"/api/v1/product/{proj_id}/pqc-readiness")
    assert pqc_res.status_code == 200
    pqc_data = pqc_res.json()
    assert "asset_count" in pqc_data

    # 6. Mosca planning
    mosca_res = client.post("/api/v1/product/mosca", json={"x": 24, "y": 12, "z": 30})
    assert mosca_res.status_code == 200
    mosca_data = mosca_res.json()
    assert mosca_data.get("status") in ["AT_RISK", "URGENT", "SAFE"]

    # 7. Asset-specific priority and roadmap lifecycle
    first_asset_id = assets[0]["asset_id"]
    prio_res = client.get(f"/api/v1/product/{proj_id}/assets/{first_asset_id}/priority?mosca_status=AT_RISK")
    assert prio_res.status_code == 200
    assert "priority" in prio_res.json()

    # 8. Roadmap lifecycle check and transition
    roadmap_res = client.get(f"/api/v1/product/{proj_id}/assets/{first_asset_id}/roadmap")
    assert roadmap_res.status_code == 200

    # Transition to EVALUATED, then IN_PLANNING
    trans_res = client.post(
        f"/api/v1/product/{proj_id}/assets/{first_asset_id}/roadmap",
        json={"requested_state": "EVALUATED", "reason": "Smoke test assessment", "operator": "e2e_runner"}
    )
    assert trans_res.status_code == 200
    assert trans_res.json().get("current_state") == "EVALUATED"

    trans_res2 = client.post(
        f"/api/v1/product/{proj_id}/assets/{first_asset_id}/roadmap",
        json={"requested_state": "IN_PLANNING", "reason": "Smoke test planning", "operator": "e2e_runner"}
    )
    assert trans_res2.status_code == 200
    assert trans_res2.json().get("current_state") == "IN_PLANNING"
