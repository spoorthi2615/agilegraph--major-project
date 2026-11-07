"""
Unit and Integration Tests for Heuristic Engine Versioning (V1 vs V2).

Verifies:
1. Heuristic V1 remains the production default across pipelines and API routes.
2. Heuristic V2 can be selected via explicit opt-in (engine_version="v2").
3. Both V1 and V2 scores coexist on every asset and graph node without destructive overwrites.
4. The /risk endpoint cleanly switches active scores based on query parameter while preserving comparisons.
5. NetworkX graph weakness propagation strictly targets files importing cryptographic libraries.
"""

import pytest
from fastapi.testclient import TestClient
import networkx as nx

from src.main import app
from src.api.routes import project_cache
from src.core.storage import default_storage
from src.risk.experimental_heuristic import (
    ExperimentalHeuristicConfig,
    propagate_graph_crypto_weakness_nx,
    derive_heuristic_label_v2
)

client = TestClient(app)


def test_derive_heuristic_label_v2_thresholds():
    """Verify calibrated threshold cutoffs: LOW < 0.18, MEDIUM [0.18, 0.38), HIGH >= 0.38."""
    assert derive_heuristic_label_v2(None) is None
    assert derive_heuristic_label_v2(0.10) == "LOW"
    assert derive_heuristic_label_v2(0.179) == "LOW"
    assert derive_heuristic_label_v2(0.18) == "MEDIUM"
    assert derive_heuristic_label_v2(0.25) == "MEDIUM"
    assert derive_heuristic_label_v2(0.379) == "MEDIUM"
    assert derive_heuristic_label_v2(0.38) == "HIGH"
    assert derive_heuristic_label_v2(0.75) == "HIGH"


def test_propagate_graph_crypto_weakness_nx():
    """Verify that NetworkX propagation only affects files importing verified crypto libraries."""
    g = nx.MultiDiGraph()
    # Direct crypto file
    g.add_node("src/crypto_cipher.py", category="file")
    g.add_node("usage_1", category="crypto_usage", algorithm="rsa", key_size=2048)
    g.add_edge("src/crypto_cipher.py", "usage_1", relationship="CONTAINS")

    # Key builder file: unobserved, imports crypto library
    g.add_node("src/key_builder.py", category="file")
    g.add_node("proj:library:cryptography.hazmat.primitives.asymmetric", category="library", library="cryptography.hazmat.primitives.asymmetric")
    g.add_edge("src/key_builder.py", "proj:library:cryptography.hazmat.primitives.asymmetric", relationship="IMPORTS")

    # Utility file: unobserved, imports non-crypto library
    g.add_node("src/string_utils.py", category="file")
    g.add_node("proj:library:json", category="library", library="json")
    g.add_edge("src/string_utils.py", "proj:library:json", relationship="IMPORTS")

    cfg = ExperimentalHeuristicConfig(attenuation_factor=0.55)
    prop_map = propagate_graph_crypto_weakness_nx(g, config=cfg)

    # Key builder should inherit weakness
    assert "src/key_builder.py" in prop_map
    assert prop_map["src/key_builder.py"] > 0.0

    # Utility file should NOT inherit weakness
    assert "src/string_utils.py" not in prop_map


def test_risk_api_engine_version_switching():
    """Verify that the API route serves V1 by default and switches to V2 when requested."""
    proj_id = "test_engine_ver_proj"
    g = nx.MultiDiGraph()
    g.add_node("src/asset1.py", category="file", v1_score=0.25, v1_label="LOW", v2_score=0.25, v2_label="MEDIUM")

    scores = [
        {
            "asset_id": "src/asset1.py",
            "score": 0.25,
            "scale": "0.0-1.0",
            "formula_version": "heuristic-v1.0",
            "engine_version": "v1",
            "heuristic_label": "LOW",
            "v1_score": 0.25,
            "v1_label": "LOW",
            "v2_score": 0.25,
            "v2_label": "MEDIUM",
            "comparison": {
                "v1": {"score": 0.25, "label": "LOW", "formula_version": "heuristic-v1.0"},
                "v2": {"score": 0.25, "label": "MEDIUM", "formula_version": "heuristic-v2.0-experimental"}
            }
        }
    ]

    project_cache[proj_id] = {
        "graph": g,
        "scores": scores,
        "provenance": {"engine_version": "v1", "available_engine_versions": ["v1", "v2"]}
    }

    try:
        # Default request (no engine_version specified) -> V1 Baseline
        res_default = client.get(f"/api/v1/projects/{proj_id}/risk")
        assert res_default.status_code == 200
        data_default = res_default.json()
        assert data_default["active_engine_version"] == "v1"
        assert data_default["assets"][0]["heuristic_label"] == "LOW"
        assert data_default["assets"][0]["formula_version"] == "heuristic-v1.0"
        assert data_default["assets"][0]["comparison"]["v2"]["label"] == "MEDIUM"

        # Explicit request with engine_version=v2 -> V2 Calibrated
        res_v2 = client.get(f"/api/v1/projects/{proj_id}/risk?engine_version=v2")
        assert res_v2.status_code == 200
        data_v2 = res_v2.json()
        assert data_v2["active_engine_version"] == "v2"
        assert data_v2["assets"][0]["heuristic_label"] == "MEDIUM"
        assert data_v2["assets"][0]["formula_version"] == "heuristic-v2.0-experimental"
        assert data_v2["assets"][0]["v1_score"] == 0.25
        assert data_v2["assets"][0]["v2_score"] == 0.25

        # Explicit request with engine_version=v1 -> matches default exactly
        res_v1 = client.get(f"/api/v1/projects/{proj_id}/risk?engine_version=v1")
        assert res_v1.status_code == 200
        data_v1 = res_v1.json()
        assert data_v1["active_engine_version"] == "v1"
        assert data_v1["assets"][0]["heuristic_label"] == "LOW"
        assert data_v1["assets"][0]["formula_version"] == "heuristic-v1.0"

    finally:
        project_cache.pop(proj_id, None)
        default_storage.delete_project(proj_id)


def test_pipeline_engine_versioning_e2e():
    """Verify that run_pipeline correctly records v1 and v2 scores and respects default vs opt-in."""
    import tempfile
    import os
    from src.pipeline.runner import run_pipeline

    with tempfile.TemporaryDirectory() as temp_dir:
        # File 1: Concrete MD5 usage
        with open(os.path.join(temp_dir, "cipher.py"), "w", encoding="utf-8") as f:
            f.write("import hashlib\nhashlib.md5().digest()\n")

        # Run pipeline with default engine (v1)
        res_v1 = run_pipeline(temp_dir, "test_proj_v1")
        assert res_v1["provenance"]["engine_version"] == "v1"
        assert "available_engine_versions" in res_v1["provenance"]
        
        scores_v1 = res_v1["scores"]
        assert len(scores_v1) >= 1
        asset_v1 = scores_v1[0]
        assert asset_v1["engine_version"] == "v1"
        assert asset_v1["formula_version"] == "heuristic-v1.0"
        assert "v1_score" in asset_v1
        assert "v2_score" in asset_v1
        assert "comparison" in asset_v1

        # Run pipeline with explicit v2
        res_v2 = run_pipeline(temp_dir, "test_proj_v2", engine_version="v2")
        assert res_v2["provenance"]["engine_version"] == "v2"
        scores_v2 = res_v2["scores"]
        asset_v2 = scores_v2[0]
        assert asset_v2["engine_version"] == "v2"
        assert asset_v2["formula_version"] == "heuristic-v2.0-experimental"
        
        # Verify score consistency: v1_score and v2_score are identical across both runs
        assert asset_v1["v1_score"] == asset_v2["v1_score"]
        assert asset_v1["v2_score"] == asset_v2["v2_score"]

