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
        
def test_fleiss_kappa():
    # 2 assets, 3 raters, 3 categories
    matrix = np.array([
        [3, 0, 0],
        [3, 0, 0]
    ])
    
    res = AgreementMetrics.fleiss_kappa(matrix)
    assert res["status"] == "COMPUTED"
    assert res["statistic"] == 1.0

def test_fleiss_kappa_insufficient_data():
    res = AgreementMetrics.fleiss_kappa(np.array([]))
    assert res["status"] == "PENDING_EXPERT_LABELS"
    assert res["statistic"] is None
