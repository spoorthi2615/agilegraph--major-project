import pytest
import os
import json
import torch
from src.ml.experiment_runner import ExperimentRunner
from src.ml.split_validator import PROTOCOL_A
from src.ml.expert_validation import ProvenanceSource


def test_runner_loads_canonical_split_and_validates_membership():
    runner = ExperimentRunner(mode="dev", ablation="STRUCTURE_ONLY", seed=42, epochs=1)
    info = runner.load_and_validate_benchmark()
    
    assert info["split_result"]["is_valid"] is True
    assert info["split_result"]["total_assets"] == 166
    assert info["split_result"]["actual_train_count"] == 92
    assert info["split_result"]["actual_val_count"] == 14
    assert info["split_result"]["actual_test_count"] == 60
    assert len(info["partitions"]["train"]) == 92
    assert len(info["partitions"]["val"]) == 14
    assert len(info["partitions"]["test"]) == 60


def test_runner_refuses_genuine_mode_without_expert_labels():
    runner = ExperimentRunner(mode="genuine", ablation="STRUCTURE_ONLY", seed=42)
    with pytest.raises(RuntimeError, match="GENUINE RESEARCH EVALUATION REFUSED"):
        runner.run()


def test_runner_ablation_dimensions_and_isolation():
    runner = ExperimentRunner(mode="dev", ablation="ALL", seed=42, epochs=1)
    info = runner.load_and_validate_benchmark()
    ag = runner.construct_benchmark_graph(info["assets"])
    consensus = {a["asset_id"]: 1 for a in info["assets"]}

    pyg_with = runner.build_pyg_data_for_ablation(ag, consensus, "WITH_BASE_RISK", info["partitions"])
    pyg_without = runner.build_pyg_data_for_ablation(ag, consensus, "WITHOUT_BASE_RISK", info["partitions"])
    pyg_struct = runner.build_pyg_data_for_ablation(ag, consensus, "STRUCTURE_ONLY", info["partitions"])

    assert pyg_with["file"].x.shape[1] == 16
    assert pyg_without["file"].x.shape[1] == 14
    assert pyg_struct["file"].x.shape[1] == 1

    # Verify identical node counts
    assert pyg_with["file"].x.shape[0] == 166
    assert pyg_without["file"].x.shape[0] == 166
    assert pyg_struct["file"].x.shape[0] == 166


def test_runner_identical_split_membership_across_ablations():
    runner = ExperimentRunner(mode="dev", ablation="ALL", seed=42, epochs=1)
    info = runner.load_and_validate_benchmark()
    ag = runner.construct_benchmark_graph(info["assets"])
    consensus = {a["asset_id"]: 1 for a in info["assets"]}

    pyg_with = runner.build_pyg_data_for_ablation(ag, consensus, "WITH_BASE_RISK", info["partitions"])
    pyg_without = runner.build_pyg_data_for_ablation(ag, consensus, "WITHOUT_BASE_RISK", info["partitions"])
    pyg_struct = runner.build_pyg_data_for_ablation(ag, consensus, "STRUCTURE_ONLY", info["partitions"])

    for data in [pyg_with, pyg_without, pyg_struct]:
        assert int(data["file"].train_mask.sum()) == 92
        assert int(data["file"].val_mask.sum()) == 14
        assert int(data["file"].test_mask.sum()) == 60

        # Disjoint masks check
        assert int((data["file"].train_mask & data["file"].val_mask).sum()) == 0
        assert int((data["file"].train_mask & data["file"].test_mask).sum()) == 0
        assert int((data["file"].val_mask & data["file"].test_mask).sum()) == 0


def test_held_out_test_split_isolation():
    """Confirms test nodes are strictly masked out of the training loop."""
    runner = ExperimentRunner(mode="dev", ablation="STRUCTURE_ONLY", seed=42, epochs=1)
    info = runner.load_and_validate_benchmark()
    ag = runner.construct_benchmark_graph(info["assets"])
    consensus = {a["asset_id"]: 1 for a in info["assets"]}

    pyg_data = runner.build_pyg_data_for_ablation(ag, consensus, "STRUCTURE_ONLY", info["partitions"])
    test_node_indices = torch.where(pyg_data["file"].test_mask)[0]
    train_node_indices = torch.where(pyg_data["file"].train_mask)[0]

    assert len(set(test_node_indices.tolist()) & set(train_node_indices.tolist())) == 0
    assert len(test_node_indices) == 60


def test_baseline_evaluation_on_test_split():
    runner = ExperimentRunner(mode="dev", ablation="STRUCTURE_ONLY", seed=42, epochs=1)
    info = runner.load_and_validate_benchmark()
    ag = runner.construct_benchmark_graph(info["assets"])

    baselines = runner.evaluate_baselines_on_test_split(ag, info["partitions"]["test"])
    assert baselines["test_asset_population"] == 60
    assert baselines["heuristic_evaluated_count"] > 0
    assert baselines["rule_based_evaluated_count"] > 0


def test_runner_dev_mode_execution_and_manifest():
    runner = ExperimentRunner(mode="dev", ablation="STRUCTURE_ONLY", seed=42, epochs=1)
    manifest = runner.run()

    assert manifest["is_synthetic_development_artifact"] is True
    assert manifest["valid_for_empirical_claims"] is False
    assert manifest["provenance"] == "SYNTHETIC_DEVELOPMENT_ONLY"
    assert manifest["mode"] == "dev"
    assert "STRUCTURE_ONLY" in manifest["ablations"]
    assert os.path.exists(manifest["ablations"]["STRUCTURE_ONLY"]["checkpoint_path"])
    assert os.path.exists(os.path.join(runner.sandbox_dir, "DEVELOPMENT_EXPERIMENT_REPORT.md"))
    assert os.path.exists(os.path.join(runner.sandbox_dir, "latest_run_manifest.json"))
