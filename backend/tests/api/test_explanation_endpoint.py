import pytest
from fastapi.testclient import TestClient
import networkx as nx

from src.main import app
from src.api.routes import project_cache
from src.core.storage import default_storage

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_mock_project():
    g = nx.MultiDiGraph()
    # Add file node and crypto usage node
    g.add_node("src/crypto.py", category="file", properties={
        "data_sensitivity": 0.8,
        "asset_criticality": 0.7,
        "internet_exposure": 0.5,
        "crypto_weakness": 0.9,
        "cve_risk": 0.0,
        "library_centrality": 0.4,
        "migration_difficulty": 0.8
    })
    g.add_node("crypto_usage_rsa", category="crypto_usage", algorithm="rsa", properties={})
    g.add_edge("src/crypto.py", "crypto_usage_rsa", relationship="uses_crypto")

    scores = [
        {
            "asset_id": "src/crypto.py",
            "score": 0.75,
            "scale": "0.0-1.0",
            "formula_version": "heuristic-v0.1",
            "missing_factors": [],
            "missing_data_policy": "RENORMALIZE",
            "weighted_contributions": {
                "crypto_weakness": {"value": 0.9, "weight": 0.25, "contribution": 0.225},
                "asset_criticality": {"value": 0.7, "weight": 0.20, "contribution": 0.14}
            }
        }
    ]

    project_cache["test_expl_proj"] = {
        "graph": g,
        "scores": scores
    }

    yield

    project_cache.pop("test_expl_proj", None)
    default_storage.delete_project("test_expl_proj")


def test_explanation_endpoint_success():
    response = client.get("/api/v1/projects/test_expl_proj/assets/src/crypto.py/explanation?epochs=10")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "src/crypto.py"
    assert data["project_id"] == "test_expl_proj"
    assert "heuristic_decomposition" in data
    assert data["heuristic_decomposition"]["status"] == "COMPUTED"
    assert data["heuristic_decomposition"]["total_risk_score"] == 0.75
    assert len(data["gnn_feature_attributions"]) > 0
    assert "caveat" in data
    assert "weak-supervision" in data["caveat"].lower()


def test_explanation_endpoint_not_found():
    response = client.get("/api/v1/projects/test_expl_proj/assets/nonexistent.py/explanation")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_explanation_endpoint_project_not_found():
    response = client.get("/api/v1/projects/nonexistent_proj/assets/src/crypto.py/explanation")
    assert response.status_code == 404

