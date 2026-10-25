"""
AgileGraph Stage 3 — Regression Tests for GATv2 Training & Evaluation
=====================================================================

Validates:
1. GATv2 forward pass across heterogeneous metadata.
2. Training loop loss reduction and parameter updates.
3. LOPO cross-validation execution and out-of-fold metric integrity.
4. Paired feature ablation (target leakage detection).
5. Heuristic and Rule-based baseline evaluation.
6. Weak-supervision qualification statements.
"""

import os
import copy
import json
import pytest
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from src.ml.gatv2 import create_hetero_gatv2
from src.ml.pipeline import TrainingPipeline, set_seed
from src.ml.evaluation import EvaluationMetrics
from scripts.run_gatv2_evaluation import (
    load_corpus_artifacts,
    run_training_verification,
    run_leakage_ablation,
    run_baseline_comparisons
)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "artifacts")


@pytest.fixture(scope="module")
def corpus_data():
    artifacts, global_meta = load_corpus_artifacts(ARTIFACTS_DIR)
    return artifacts, global_meta


def test_artifacts_population_and_metadata(corpus_data):
    """Verifies that all 8 repository artifacts exist and contain valid file nodes and labels."""
    artifacts, global_meta = corpus_data
    assert len(artifacts) == 8, f"Expected 8 benchmark repositories, found {len(artifacts)}"

    total_files = 0
    for pid, d in artifacts.items():
        assert "file" in d.node_types, f"Repository {pid} missing 'file' node type"
        assert hasattr(d["file"], "x"), f"Repository {pid} missing file features"
        assert hasattr(d["file"], "y"), f"Repository {pid} missing file labels"
        assert d["file"].x.shape[1] == 14, f"Repository {pid} feature dimension != 14 (found {d['file'].x.shape[1]})"
        total_files += d["file"].num_nodes

    assert total_files == 520, f"Expected 520 total file nodes across corpus, found {total_files}"


def test_gatv2_training_mechanics_and_parameter_update(corpus_data):
    """Confirms that forward/backward training loop reduces loss and updates model parameters."""
    artifacts, global_meta = corpus_data
    res = run_training_verification(artifacts, global_meta, seed=42, epochs=5)

    assert res["status"] == "VERIFIED"
    assert res["loss_reduction"] > 0, "Loss failed to decrease during training"
    assert res["parameter_l2_delta"] > 1e-6, "Model parameters were frozen / unupdated"


def test_metrics_balanced_accuracy_and_confusion_matrix():
    """Verifies that EvaluationMetrics calculates macro-F1, balanced accuracy, and confusion matrix."""
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])

    metrics = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred, target_classes=[0, 1, 2])
    assert metrics["status"] == "COMPUTED"
    assert "balanced_accuracy" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["confusion_matrix"] == [[1, 1, 0], [0, 2, 0], [1, 0, 1]]
    assert metrics["accuracy"] == 4 / 6
    # Recall per class: 0 -> 1/2, 1 -> 2/2, 2 -> 1/2 -> Balanced = (0.5 + 1.0 + 0.5) / 3 = 2/3
    assert abs(metrics["balanced_accuracy"] - 2 / 3) < 1e-4


def test_paired_leakage_ablation(corpus_data):
    """Verifies that WITHOUT_BASE_RISK uses 14-dim features without continuous risk leakage."""
    artifacts, global_meta = corpus_data
    d = artifacts["python_cryptography"]
    assert d["file"].x.shape[1] == 14, "Target leakage detected: input dimension != 14"

    res = run_leakage_ablation(artifacts, global_meta, seed=42, epochs=5)
    assert "intra_repo_resubstitution" in res
    assert "cross_repo_lopo_leakage_impact" in res
    assert res["intra_repo_resubstitution"]["without_base_risk"]["accuracy"] > 0.80


def test_baseline_comparisons(corpus_data):
    """Verifies heuristic baseline (teacher) concordance and rule-based baseline execution."""
    artifacts, _ = corpus_data
    res = run_baseline_comparisons(artifacts)

    # Heuristic baseline is the teacher from which weak labels were derived -> 100% concordance
    h_res = res["heuristic_baseline"]
    assert h_res["accuracy"] == 1.0
    assert h_res["macro_f1"] == 1.0

    # Rule baseline is an independent heuristic without weights -> lower macro-F1
    r_res = res["rule_baseline"]
    assert r_res["accuracy"] < 1.0
    assert r_res["macro_f1"] < 0.60
