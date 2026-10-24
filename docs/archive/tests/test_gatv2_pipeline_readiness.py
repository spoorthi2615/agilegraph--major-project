import pytest
import os
import json
import torch
import numpy as np

from src.ml.features import FeatureConfig, extract_node_features
from src.ml.split_validator import PROTOCOL_A, validate_repository_disjointness, partition_assets_by_split
from src.ml.explainability import (
    explain_heuristic_decomposition,
    compute_gradient_feature_importance,
    estimate_risk_reduction
)
from src.risk.score import RiskScoreResult, MissingDataPolicy, FactorContribution
from src.ml.synthetic_dev_sandbox import SyntheticDevSandbox
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge


# =====================================================================
# Phase 2: Leakage Ablation Feature Dimension Tests
# =====================================================================

def test_feature_ablation_dimensions_and_isolation():
    props = {
        "risk_factors": {
            "data_sensitivity": 0.8,
            "asset_criticality": 0.7,
            "internet_exposure": 1.0,
            "crypto_weakness": 0.9,
            "cve_risk": 0.5,
            "library_centrality": 0.4,
            "migration_difficulty": 0.6
        },
        "base_risk": 0.77
    }

    # 1. WITH_BASE_RISK: [7 factors, base_risk] + [7 factor masks, base_risk mask] = 16 dimensions
    feat_with = extract_node_features(props, FeatureConfig(include_base_risk=True, structure_only=False))
    assert feat_with.shape == (16,)
    # Factors are indices 0..6, base_risk is index 7
    # Missingness masks are indices 8..14, mask_base_risk is index 15
    assert abs(feat_with[7].item() - 0.77) < 1e-4  # base_risk is present at index 7
    assert feat_with[15].item() == 0.0  # missingness mask for base_risk is 0 at index 15

    # 2. WITHOUT_BASE_RISK: 7 context factors + 7 missing masks = 14 dimensions (NO scalar prior)
    feat_without = extract_node_features(props, FeatureConfig(include_base_risk=False, structure_only=False))
    assert feat_without.shape == (14,)
    # base_risk value 0.77 must NOT appear in feat_without
    assert not any(abs(v.item() - 0.77) < 1e-4 for v in feat_without)

    # 3. STRUCTURE_ONLY: exactly 1 constant dummy token [0.0]
    feat_struct = extract_node_features(props, FeatureConfig(include_base_risk=False, structure_only=True))
    assert feat_struct.shape == (1,)
    assert feat_struct[0].item() == 0.0


def test_structure_only_perturbation_invariance():
    """Perturbing or corrupting heuristic inputs cannot change structure_only model inputs."""
    props_clean = {
        "risk_factors": {"data_sensitivity": 0.1, "crypto_weakness": 0.1},
        "base_risk": 0.10
    }
    props_perturbed = {
        "risk_factors": {"data_sensitivity": 1.0, "crypto_weakness": 1.0, "asset_criticality": 1.0},
        "base_risk": 0.99
    }

    feat_clean = extract_node_features(props_clean, FeatureConfig(structure_only=True))
    feat_perturbed = extract_node_features(props_perturbed, FeatureConfig(structure_only=True))

    assert torch.equal(feat_clean, feat_perturbed)
    assert feat_clean.shape == (1,)


# =====================================================================
# Phase 3: Repository-Disjoint Evaluation Split Tests
# =====================================================================

def test_protocol_a_repository_disjointness():
    validation = validate_repository_disjointness(PROTOCOL_A)
    assert validation["is_disjoint"] is True
    assert len(validation["train_val_overlap"]) == 0
    assert len(validation["train_test_overlap"]) == 0
    assert len(validation["val_test_overlap"]) == 0


def test_protocol_a_asset_partition_counts():
    pkg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "dataset", "annotation", "sample_annotation_package.json"
    )
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    assets = pkg.get("assets", [])
    partitions = partition_assets_by_split(assets, PROTOCOL_A)

    assert len(partitions["unassigned"]) == 0
    assert len(partitions["train"]) == PROTOCOL_A.expected_train_count  # 92
    assert len(partitions["val"]) == PROTOCOL_A.expected_val_count      # 14
    assert len(partitions["test"]) == PROTOCOL_A.expected_test_count    # 60
    assert len(partitions["train"]) + len(partitions["val"]) + len(partitions["test"]) == 166


def test_split_integrity_canonical_dataset():
    """Validates the canonical 166-asset package passes all strict split integrity checks."""
    from src.ml.split_validator import validate_split_integrity

    pkg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "dataset", "annotation", "sample_annotation_package.json"
    )
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    res = validate_split_integrity(pkg["assets"], PROTOCOL_A)
    assert res["is_valid"] is True
    assert res["errors"] == []
    assert res["total_assets"] == 166
    assert res["unique_asset_ids"] == 166
    assert res["actual_train_count"] == 92
    assert res["actual_val_count"] == 14
    assert res["actual_test_count"] == 60

    # Verify exact per-repo distribution
    expected_repo_counts = {
        "python_cryptography": 50,
        "python_itsdangerous": 7,
        "python_bcrypt": 2,
        "java_jjwt": 35,
        "java_java_jwt": 20,
        "go_crypto": 25,
        "go_jwt": 15,
        "go_jwt_go": 12
    }
    assert res["repo_counts"] == expected_repo_counts


def test_split_integrity_rejects_duplicate_asset_ids():
    from src.ml.split_validator import validate_split_integrity

    mock_assets = [
        {"asset_id": "go_crypto:a.go", "project_id": "go_crypto"},
        {"asset_id": "go_crypto:a.go", "project_id": "go_crypto"},  # DUPLICATE!
    ]
    res = validate_split_integrity(mock_assets, PROTOCOL_A)
    assert res["is_valid"] is False
    assert any("Duplicate asset IDs" in err for err in res["errors"])


def test_split_integrity_rejects_unknown_repositories():
    from src.ml.split_validator import validate_split_integrity, SplitDefinition

    bad_split = SplitDefinition(
        train_repos=["unapproved_secret_repo"],
        val_repos=["python_bcrypt"],
        test_repos=["go_crypto"],
        expected_train_count=1,
        expected_val_count=2,
        expected_test_count=25
    )
    mock_assets = [
        {"asset_id": "unapproved_secret_repo:x.py", "project_id": "unapproved_secret_repo"}
    ]
    res = validate_split_integrity(mock_assets, bad_split)
    assert res["is_valid"] is False
    assert any("unknown repositories" in err for err in res["errors"])


# =====================================================================
# Phase 6: Explainability Suite Tests
# =====================================================================

def test_explain_heuristic_decomposition():
    contributions = {
        "crypto_weakness": FactorContribution(value=0.9, weight=0.3, contribution=0.27),
        "asset_criticality": FactorContribution(value=0.8, weight=0.2, contribution=0.16),
    }
    res = RiskScoreResult(
        score=0.43,
        formula_version="heuristic-v0.1",
        weights={"crypto_weakness": 0.3, "asset_criticality": 0.2},
        factors={"crypto_weakness": {"value": 0.9}, "asset_criticality": {"value": 0.8}},
        weighted_contributions=contributions,
        missing_factors=["data_sensitivity"],
        missing_data_policy=MissingDataPolicy.RENORMALIZE,
        assumptions=[]
    )

    decomp = explain_heuristic_decomposition(res)
    assert decomp["status"] == "COMPUTED"
    assert decomp["total_risk_score"] == 0.43
    assert "crypto_weakness" in decomp["factor_contributions"]
    assert decomp["factor_contributions"]["crypto_weakness"]["absolute_contribution"] == 0.27


def test_gradient_feature_importance_saliency():
    sandbox = SyntheticDevSandbox(seed=42)
    ag = AgileGraph()
    ag.add_node(GraphNode(
        id="f1",
        category="file",
        properties={"risk_factors": {"data_sensitivity": 0.8, "crypto_weakness": 0.9}, "base_risk": 0.85}
    ))
    ag.add_node(GraphNode(
        id="c1",
        category="crypto_usage",
        properties={"algorithm": "RSA"}
    ))
    ag.add_edge(GraphEdge(source_id="f1", target_id="c1", relationship="USES_CRYPTO"))
    ag.add_edge(GraphEdge(source_id="c1", target_id="f1", relationship="USED_BY_FILE"))

    pyg_data = sandbox.build_synthetic_pyg_data(ag, {"f1": 2}, FeatureConfig(include_base_risk=False))

    from src.ml.gatv2 import create_hetero_gatv2
    model = create_hetero_gatv2(pyg_data.metadata(), hidden_channels=16, out_channels=3, num_heads=2)

    saliency_result = compute_gradient_feature_importance(model, pyg_data, target_node_category="file", target_node_idx=0)
    assert saliency_result["status"] == "COMPUTED"
    assert "feature_attributions" in saliency_result
    assert len(saliency_result["feature_attributions"]) == 14
    assert "data_sensitivity" in saliency_result["feature_attributions"]


def test_estimate_risk_reduction():
    res = estimate_risk_reduction(
        current_score=0.85,
        mitigated_factors={"crypto_weakness": 0.0},
        weights={"crypto_weakness": 0.30}
    )
    assert res["status"] == "COMPUTED"
    assert res["baseline_risk"] == 0.85
    assert "crypto_weakness" in res["mitigated_factors"]
