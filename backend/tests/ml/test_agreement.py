import pytest
import numpy as np
from src.ml.agreement import AgreementMetrics
from src.ml.expert_validation import ExpertLabelClass

def test_cohens_kappa_insufficient_data():
    # SYNTHETIC_TEST_DATA
    # NOT REAL EXPERT VALIDATION
    
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.UNKNOWN]
    y2 = [ExpertLabelClass.UNKNOWN, ExpertLabelClass.LOW]
    
    with pytest.raises(ValueError):
        AgreementMetrics.cohens_kappa(y1, y2)
        
def test_fleiss_kappa():
    # SYNTHETIC_TEST_DATA
    # NOT REAL EXPERT VALIDATION
    
    # 2 assets, 3 raters, 3 categories
    matrix = np.array([
        [3, 0, 0],
        [3, 0, 0]
    ])
    
    k = AgreementMetrics.fleiss_kappa(matrix)
    assert k == 1.0
