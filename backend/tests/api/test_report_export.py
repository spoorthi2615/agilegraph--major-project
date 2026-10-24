import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.api.routes import project_cache
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge

client = TestClient(app)


@pytest.fixture(autouse=True)
def populate_test_project():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="test_repo:crypto.py", category="file"))
    ag.add_node(GraphNode(id="cu_rsa", category="crypto_usage", properties={"algorithm": "rsa", "key_size": 1024}))
    ag.add_edge(GraphEdge(source_id="test_repo:crypto.py", target_id="cu_rsa", relationship="CONTAINS"))

    project_cache["test_export_proj"] = {
        "graph": ag.G,
        "scores": [
            {
                "asset_id": "test_repo:crypto.py",
                "score": 0.85,
                "missing_factors": [],
                "missing_data_policy": "RENORMALIZE",
                "factors": {
                    "crypto_weakness": {"value": 1.0, "source": "ast"},
                    "asset_criticality": {"value": 0.5, "source": "in_degree"}
                },
                "weights": {
                    "crypto_weakness": 0.25,
                    "asset_criticality": 0.15
                },
                "weighted_contributions": {
                    "crypto_weakness": {"contribution": 0.25},
                    "asset_criticality": {"contribution": 0.075}
                },
                "assumptions": ["Assumed classical RSA-1024 vulnerable to Shor's algorithm"]
            }
        ],
        "provenance": {
            "scanned_files": 1,
            "git_sha": "abc123def456",
            "osv_enrichment_date": "2026-10-24"
        },
        "missing_data_policy": "RENORMALIZE"
    }
    yield
    project_cache.pop("test_export_proj", None)


def test_export_report_json():
    res = client.get("/api/v1/projects/test_export_proj/report/json")
    assert res.status_code == 200
    data = res.json()
    assert "report_metadata" in data
    meta = data["report_metadata"]
    assert meta["project_id"] == "test_export_proj"
    assert meta["git_sha"] == "abc123def456"
    assert "config_hash" in meta
    assert meta["missing_evidence_policy"] == "RENORMALIZE"
    assert "operational_disclaimer" in meta
    assert "operational estimates" in meta["operational_disclaimer"].lower()
    assert "scanner_scope" in data
    assert "factor_weights" in data
    assert len(data["assets"]) == 1


def test_export_report_markdown():
    res = client.get("/api/v1/projects/test_export_proj/report/markdown")
    assert res.status_code == 200
    content = res.text
    assert "# AgileGraph Security Audit Report" in content
    assert "Operational Estimate Disclaimer" in content
    assert "Git SHA" in content
    assert "Config Hash" in content
    assert "Declared Scanner Scope" in content


def test_export_report_not_found():
    res = client.get("/api/v1/projects/non_existent_proj_xyz/report/json")
    assert res.status_code == 404
    res_md = client.get("/api/v1/projects/non_existent_proj_xyz/report/markdown")
    assert res_md.status_code == 404
