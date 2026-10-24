import pytest
import os
import json
import torch
from src.ml.synthetic_dev_sandbox import SyntheticDevSandbox
from src.ml.features import FeatureConfig
from src.graph.graph import AgileGraph


from src.graph.schema import GraphNode, GraphEdge


@pytest.fixture
def mock_graph_with_assets():
    ag = AgileGraph()
    
    # Add files
    ag.add_node(GraphNode(
        id="f1",
        category="file",
        properties={
            "risk_factors": {"data_sensitivity": 0.8, "crypto_weakness": 0.9},
            "base_risk": 0.85
        }
    ))
    ag.add_node(GraphNode(
        id="f2",
        category="file",
        properties={
            "risk_factors": {"data_sensitivity": 0.2, "crypto_weakness": 0.1},
            "base_risk": 0.15
        }
    ))
    ag.add_node(GraphNode(
        id="f3",
        category="file",
        properties={
            "risk_factors": {"data_sensitivity": 0.5, "crypto_weakness": 0.5},
            "base_risk": 0.50
        }
    ))

    # Add crypto usage
    ag.add_node(GraphNode(
        id="c1",
        category="crypto_usage",
        properties={"algorithm": "RSA"}
    ))
    ag.add_edge(GraphEdge(source_id="f1", target_id="c1", relationship="USES_CRYPTO"))
    ag.add_edge(GraphEdge(source_id="c1", target_id="f1", relationship="USED_BY_FILE"))

    return ag


def test_synthetic_dev_sandbox_dataset_generation():
    sandbox = SyntheticDevSandbox(seed=42)
    assets = [
        {"asset_id": "test_repo:f1", "project_id": "test_repo"},
        {"asset_id": "test_repo:f2", "project_id": "test_repo"},
    ]
    manifest = sandbox.generate_synthetic_development_dataset(assets, num_raters=4)

    assert manifest["is_synthetic_development_artifact"] is True
    assert manifest["valid_for_empirical_claims"] is False
    assert manifest["provenance"] == "SYNTHETIC_DEVELOPMENT_ONLY"
    assert len(manifest["consensus_labels"]) == 2
    assert os.path.exists(os.path.join(sandbox.SANDBOX_DIR, "synthetic_dataset_manifest.json"))


def test_synthetic_dev_sandbox_training_mechanics(mock_graph_with_assets):
    sandbox = SyntheticDevSandbox(seed=42)
    consensus = {"f1": 2, "f2": 0, "f3": 1}

    pyg_data = sandbox.build_synthetic_pyg_data(
        ag=mock_graph_with_assets,
        consensus_labels=consensus,
        feature_config=FeatureConfig(include_base_risk=False)
    )

    assert "file" in pyg_data.node_types
    assert pyg_data["file"].y.shape[0] == 3
    assert (pyg_data["file"].y >= 0).sum().item() == 3

    # Run training smoke test
    results = sandbox.run_synthetic_training_smoke_test(pyg_data, epochs=3, hidden_dim=16)

    assert results["is_synthetic_development_artifact"] is True
    assert results["valid_for_empirical_claims"] is False
    assert results["provenance"] == "SYNTHETIC_DEVELOPMENT_ONLY"
    assert results["epochs_trained"] == 3
    assert os.path.exists(results["checkpoint_path"])
    assert "metrics" in results
    assert results["metrics"]["status"] == "COMPUTED"
