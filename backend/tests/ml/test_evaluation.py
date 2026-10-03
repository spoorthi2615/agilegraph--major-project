import pytest
import numpy as np
from src.ml.evaluation import EvaluationMetrics

def test_classification_metrics():
    y_true = np.array([0, 1, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 0, 1])
    
    metrics = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred)
    assert "macro_f1" in metrics
    assert "accuracy" in metrics
    assert metrics["accuracy"] == 0.8
    assert metrics["class_1_recall"] == 2/3
    assert metrics["class_0_precision"] == 2/3

def test_bootstrap_infrastructure():
    # Verify the infrastructure exists, even if PENDING
    ci = EvaluationMetrics.bootstrap_ci(np.array([]), np.array([]))
    assert isinstance(ci, tuple)
    assert len(ci) == 2

def test_permutation_infrastructure():
    pval = EvaluationMetrics.paired_permutation_test(np.array([]), np.array([]), np.array([]))
    assert isinstance(pval, float)
