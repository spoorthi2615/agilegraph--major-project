import pytest
import numpy as np
from src.ml.agreement import AgreementMetrics
from src.ml.expert_validation import ExpertLabelClass

def test_cohens_kappa_insufficient_data():
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.UNKNOWN]
    y2 = [ExpertLabelClass.UNKNOWN, ExpertLabelClass.LOW]

    res = AgreementMetrics.cohens_kappa(y1, y2)
    assert res["status"] == "PENDING_EXPERT_LABELS"
    assert res["statistic"] is None

def test_cohens_kappa_perfect_agreement():
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW]
    y2 = [ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW]
    res = AgreementMetrics.cohens_kappa(y1, y2)
    assert res["status"] == "COMPUTED"
    assert res["statistic"] == pytest.approx(1.0)

def test_cohens_kappa_disagreement():
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.HIGH, ExpertLabelClass.HIGH]
    y2 = [ExpertLabelClass.LOW, ExpertLabelClass.LOW, ExpertLabelClass.LOW]
    res = AgreementMetrics.cohens_kappa(y1, y2)
    assert res["status"] == "COMPUTED"
    assert res["statistic"] <= 0.0

def test_cohens_kappa_partial():
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW, ExpertLabelClass.HIGH, ExpertLabelClass.LOW]
    y2 = [ExpertLabelClass.HIGH, ExpertLabelClass.LOW, ExpertLabelClass.LOW, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW]
    res = AgreementMetrics.cohens_kappa(y1, y2)
    assert res["status"] == "COMPUTED"
    # Expected value depends on exact formulation, but should be between 0 and 1
    assert 0.0 < res["statistic"] < 1.0

def test_fleiss_kappa():
    # 2 assets, 3 raters, 3 categories
    matrix = np.array([
        [3, 0, 0],
        [3, 0, 0]
    ])

    res = AgreementMetrics.fleiss_kappa(matrix)
    assert res["status"] == "COMPUTED"
    assert res["statistic"] == 1.0

def test_fleiss_kappa_disagreement():
    # 2 assets, 3 raters, 3 categories
    matrix = np.array([
        [1, 1, 1],
        [1, 1, 1]
    ])
    res = AgreementMetrics.fleiss_kappa(matrix)
    assert res["status"] == "COMPUTED"
    # perfect disagreement => negative or zero kappa depending on p_e
    assert res["statistic"] <= 0.0

def test_fleiss_kappa_insufficient_data():
    res = AgreementMetrics.fleiss_kappa(np.array([]))
    assert res["status"] == "PENDING_EXPERT_LABELS"
    assert res["statistic"] is None

def test_fleiss_kappa_malformed_unequal_raters():
    matrix = np.array([
        [2, 0, 0],
        [1, 0, 0]
    ])
    with pytest.raises(ValueError, match="Number of raters per item must be equal"):
        AgreementMetrics.fleiss_kappa(matrix)

def test_fleiss_kappa_negative_counts():
    matrix = np.array([
        [3, -1, 0],
        [2, 0, 0]
    ])
    with pytest.raises(ValueError, match="Ratings matrix cannot contain negative counts"):
        AgreementMetrics.fleiss_kappa(matrix)
