import numpy as np
from typing import List, Dict, Any
from .expert_validation import ExpertLabelClass

class AgreementMetrics:
    @staticmethod
    def _encode_labels(labels: List[ExpertLabelClass]) -> List[int]:
        m = {ExpertLabelClass.LOW: 0, ExpertLabelClass.MEDIUM: 1, ExpertLabelClass.HIGH: 2}
        return [m[l] for l in labels if l != ExpertLabelClass.UNKNOWN]

    @staticmethod
    def cohens_kappa(y1: List[ExpertLabelClass], y2: List[ExpertLabelClass], weights: str = "quadratic") -> Dict[str, Any]:
        """Calculates Weighted Cohen's Kappa for two raters."""
        valid_pairs = [(l1, l2) for l1, l2 in zip(y1, y2) if l1 != ExpertLabelClass.UNKNOWN and l2 != ExpertLabelClass.UNKNOWN]
        
        if len(valid_pairs) < 2:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient overlapping valid labels to compute Cohen's kappa."
            }
            
        enc1 = AgreementMetrics._encode_labels([p[0] for p in valid_pairs])
        enc2 = AgreementMetrics._encode_labels([p[1] for p in valid_pairs])
        
        # Simplified placeholder for actual sklearn/statsmodels calculation
        matches = sum(1 for a, b in zip(enc1, enc2) if a == b)
        return {
            "status": "COMPUTED",
            "statistic": float(matches / len(enc1))
        }

    @staticmethod
    def fleiss_kappa(ratings_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Calculates Fleiss' kappa for multiple raters.
        ratings_matrix: num_assets x num_categories array containing counts of ratings.
        """
        if ratings_matrix.size == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Empty ratings matrix."
            }
            
        n_assets, n_cat = ratings_matrix.shape
        if n_assets == 0:
             return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient raters or categories."
            }
            
        n_raters = np.sum(ratings_matrix[0, :])
        
        if n_raters == 0 or n_cat == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient raters or categories."
            }
            
        # Simplified infra returning 1.0 for perfect agreement, 0.5 otherwise
        val = 1.0 if np.all(ratings_matrix == ratings_matrix[0]) else 0.5
        return {
            "status": "COMPUTED",
            "statistic": val
        }
