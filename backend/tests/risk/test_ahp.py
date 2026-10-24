import pytest
import numpy as np
from src.risk.ahp import (
    AHPEngine,
    HEURISTIC_FACTORS,
    PairwiseComparison,
    AHPSurveyResponse
)


def test_questionnaire_template_generation():
    template = AHPEngine.generate_questionnaire_template()
    # 7 factors -> 7 * 6 / 2 = 21 pairwise comparisons
    assert len(template) == 21
    assert template[0]["question_id"] == "Q01"
    assert template[0]["factor_a"] == "data_sensitivity"
    assert template[0]["factor_b"] == "asset_criticality"


def test_matrix_construction_and_reciprocity():
    comparisons = [
        PairwiseComparison(factor_a="crypto_weakness", factor_b="asset_criticality", relative_importance=3.0),
        PairwiseComparison(factor_a="internet_exposure", factor_b="data_sensitivity", relative_importance=0.5), # 1/2
    ]
    matrix = AHPEngine.build_matrix_from_comparisons(comparisons)
    assert matrix.shape == (7, 7)
    # Diagonal must be 1.0
    for i in range(7):
        assert matrix[i, i] == 1.0

    f_idx = {name: idx for idx, name in enumerate(HEURISTIC_FACTORS)}
    cw_idx = f_idx["crypto_weakness"]
    ac_idx = f_idx["asset_criticality"]
    assert matrix[cw_idx, ac_idx] == 3.0
    assert abs(matrix[ac_idx, cw_idx] - 1/3) < 1e-5


def test_derive_weights_perfect_consistency():
    # If all items are equally important, matrix is all 1s
    n = 7
    matrix = np.ones((n, n), dtype=float)
    res = AHPEngine.derive_weights(matrix)

    assert res.status == "COMPUTED"
    assert res.is_consistent is True
    assert abs(res.consistency_ratio) < 1e-4
    assert abs(res.lambda_max - 7.0) < 1e-4

    # Each weight should be ~ 1/7 = 0.14286
    for k, w in res.weights.items():
        assert abs(w - (1.0 / 7.0)) < 1e-3

    # Weights must sum to 1.0
    assert abs(sum(res.weights.values()) - 1.0) < 1e-4


def test_derive_weights_inconsistent_detection():
    # Build an intentionally highly inconsistent matrix
    # A > B (9), B > C (9), but C > A (9)
    matrix = np.ones((7, 7), dtype=float)
    matrix[0, 1] = 9.0
    matrix[1, 0] = 1/9
    matrix[1, 2] = 9.0
    matrix[2, 1] = 1/9
    matrix[2, 0] = 9.0  # Inconsistent cycle!
    matrix[0, 2] = 1/9

    res = AHPEngine.derive_weights(matrix)
    assert res.status == "COMPUTED"
    assert res.is_consistent is False
    assert res.consistency_ratio > 0.10
    assert "Inconsistent" in res.message


def test_group_geometric_mean_aggregation():
    # Two expert matrices
    n = 7
    m1 = np.ones((n, n), dtype=float)
    m1[0, 1] = 4.0
    m1[1, 0] = 0.25

    m2 = np.ones((n, n), dtype=float)
    m2[0, 1] = 1.0
    m2[1, 0] = 1.0

    # Geometric mean between 4 and 1 is sqrt(4*1) = 2
    agg = AHPEngine.aggregate_group_weights([m1, m2])
    assert agg.status == "COMPUTED"
    assert agg.is_consistent is True
    # Factor 0 should have higher weight than Factor 1
    assert agg.weights[HEURISTIC_FACTORS[0]] > agg.weights[HEURISTIC_FACTORS[1]]


def test_empty_group_aggregation():
    agg = AHPEngine.aggregate_group_weights([])
    assert agg.status == "NO_MATRICES_PROVIDED"
    assert agg.is_consistent is False
