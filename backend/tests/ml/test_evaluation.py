import pytest
import numpy as np
from src.ml.evaluation import EvaluationMetrics

def test_classification_metrics_computed():
    y_true = np.array([0, 1, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 0, 1])
    
    metrics = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred)
    assert metrics["status"] == "COMPUTED"
    assert "macro_f1" in metrics
    assert "accuracy" in metrics
    assert metrics["accuracy"] == 0.8
    assert metrics["class_1_recall"] == 2/3
    assert metrics["class_0_precision"] == 2/3

def test_classification_metrics_pending():
    metrics = EvaluationMetrics.calculate_classification_metrics(np.array([]), np.array([]))
    assert metrics["status"] == "PENDING_EXPERT_LABELS"
    assert metrics["macro_f1"] is None
    assert metrics["accuracy"] is None

def test_bootstrap_infrastructure_pending():
    ci = EvaluationMetrics.bootstrap_ci(np.array([]), np.array([]))
    assert ci["status"] == "PENDING_EXPERT_LABELS"
    assert ci["confidence_interval"] is None

def test_permutation_infrastructure_pending():
    pval = EvaluationMetrics.paired_permutation_test(np.array([]), np.array([]), np.array([]))
    assert pval["status"] == "PENDING_EXPERT_LABELS"
    assert pval["p_value"] is None
    assert pval["statistic"] is None
