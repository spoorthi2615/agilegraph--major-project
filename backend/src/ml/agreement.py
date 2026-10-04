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
        
        from sklearn.metrics import cohen_kappa_score
        
        # Explicit check for pure agreement and disagreement cases handled by sklearn
        score = cohen_kappa_score(enc1, enc2, weights=weights)
        return {
            "status": "COMPUTED",
            "statistic": float(score)
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
            
        # Fleiss' Kappa mathematically correct implementation
        # N = n_assets, n = n_raters, k = n_cat
        # P_i = 1 / (n * (n - 1)) * sum(n_ij * (n_ij - 1))
        # P_bar = sum(P_i) / N
        # p_j = sum(n_ij) / (N * n)
        # P_e_bar = sum(p_j^2)
        # kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
        
        N = n_assets
        n = n_raters
        
        if n <= 1:
            return {
                "status": "NOT_IMPLEMENTED",
                "statistic": None,
                "message": "Fleiss kappa requires at least 2 raters."
            }
            
        P_i = np.sum(ratings_matrix * (ratings_matrix - 1), axis=1) / (n * (n - 1))
        P_bar = np.mean(P_i)
        
        p_j = np.sum(ratings_matrix, axis=0) / (N * n)
        P_e_bar = np.sum(p_j ** 2)
        
        if P_e_bar == 1.0:
            # If P_e_bar is 1, then all raters agreed completely on one category.
            return {
                "status": "COMPUTED",
                "statistic": 1.0
            }
            
        kappa = (P_bar - P_e_bar) / (1 - P_e_bar)
        
        return {
            "status": "COMPUTED",
            "statistic": float(kappa)
        }
