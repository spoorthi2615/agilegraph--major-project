"""
Inter-Annotator Agreement and Statistical Evaluation Module for AgileGraph.

Implements standard psychometric and machine learning agreement metrics:
- Weighted Cohen's Kappa (linear & quadratic penalty for ordinal risk categories)
- Fleiss' Kappa for multi-expert panel consensus
- Macro-F1 with zero-division protection
- Non-parametric Percentile Bootstrap Confidence Intervals
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
import numpy as np
from sklearn.metrics import cohen_kappa_score, f1_score
from src.ml.expert_validation import ExpertLabelClass, LABEL_TO_INT


class AgreementMetrics:
    """
    Computes rigorous statistical agreement metrics between human experts
    and against machine-learned or heuristic risk categorizations.
    """

    @staticmethod
    def cohens_kappa(
        rater1: List[int],
        rater2: List[int],
        weights: Optional[str] = "linear"
    ) -> float:
        """
        Computes Cohen's Kappa between two raters.
        Weights:
          - "linear": Linear penalty for ordinal distance (|i - j|)
          - "quadratic": Quadratic penalty ((i - j)^2)
          - None: Unweighted binary agreement
        """
        if len(rater1) != len(rater2) or len(rater1) == 0:
            raise ValueError("Rater sequences must be non-empty and of identical length.")
        
        score = cohen_kappa_score(rater1, rater2, weights=weights)
        return float(score) if not np.isnan(score) else 0.0

    @staticmethod
    def pairwise_kappas(
        rater_dict: Dict[str, List[int]],
        weights: Optional[str] = "linear"
    ) -> Dict[str, Any]:
        """
        Computes pairwise Cohen's Kappa across all pairs of raters in a panel.
        """
        raters = list(rater_dict.keys())
        pairs = {}
        values = []

        for i in range(len(raters)):
            for j in range(i + 1, len(raters)):
                r1 = raters[i]
                r2 = raters[j]
                k = AgreementMetrics.cohens_kappa(rater_dict[r1], rater_dict[r2], weights=weights)
                pair_name = f"{r1}_vs_{r2}"
                pairs[pair_name] = round(k, 4)
                values.append(k)

        mean_kappa = float(np.mean(values)) if values else 0.0
        return {
            "pairwise": pairs,
            "mean_pairwise_kappa": round(mean_kappa, 4),
            "num_pairs": len(pairs)
        }

    @staticmethod
    def fleiss_kappa(ratings_matrix: np.ndarray) -> float:
        """
        Computes Fleiss' Kappa for inter-annotator agreement among m raters on N subjects.
        ratings_matrix: shape (N, k) where:
          - N: number of subjects (assets)
          - k: number of categories (3: LOW, MEDIUM, HIGH)
          - ratings_matrix[i, j]: count of raters who assigned subject i to category j.
        """
        if ratings_matrix.ndim != 2:
            raise ValueError("ratings_matrix must be 2-dimensional (N subjects x k categories).")

        n_subjects, n_categories = ratings_matrix.shape
        if n_subjects == 0 or n_categories == 0:
            return 0.0

        n_raters_per_subject = np.sum(ratings_matrix, axis=1)
        # Verify consistent number of raters per subject
        m = n_raters_per_subject[0]
        if not np.all(n_raters_per_subject == m) or m <= 1:
            raise ValueError(f"Each subject must have the exact same number of raters m > 1 (found: {n_raters_per_subject}).")

        # p_j = proportion of all assignments made to category j
        total_assignments = n_subjects * m
        p_j = np.sum(ratings_matrix, axis=0) / total_assignments

        # P_i = degree of agreement among raters for subject i
        sum_nij_sq = np.sum(ratings_matrix ** 2, axis=1)
        p_i = (sum_nij_sq - m) / (m * (m - 1))

        # Mean P_i across all subjects
        p_bar = np.mean(p_i)
        # Expected agreement by chance
        p_bar_e = np.sum(p_j ** 2)

        if np.isclose(1.0, p_bar_e):
            return 1.0

        kappa = (p_bar - p_bar_e) / (1.0 - p_bar_e)
        return float(round(kappa, 4))

    @staticmethod
    def macro_f1(y_true: List[int], y_pred: List[int]) -> float:
        """
        Computes unweighted macro-averaged F1 score across all classes with zero-division handling.
        """
        if len(y_true) != len(y_pred) or len(y_true) == 0:
            raise ValueError("Sequences must be non-empty and equal in length.")
        
        f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
        return float(round(f1, 4))

    @staticmethod
    def bootstrap_confidence_interval(
        metric_fn: Callable[[List[int], List[int]], float],
        y_true: List[int],
        y_pred: List[int],
        n_bootstraps: int = 1000,
        confidence_level: float = 0.95,
        seed: int = 42
    ) -> Dict[str, float]:
        """
        Computes empirical percentile bootstrap confidence intervals.
        """
        rng = np.random.RandomState(seed)
        n = len(y_true)
        if n == 0 or len(y_pred) != n:
            raise ValueError("Arrays must be non-empty and of equal length.")

        point_est = metric_fn(y_true, y_pred)
        bootstrap_scores = []

        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)

        for _ in range(n_bootstraps):
            indices = rng.randint(0, n, size=n)
            bs_true = y_true_arr[indices].tolist()
            bs_pred = y_pred_arr[indices].tolist()
            score = metric_fn(bs_true, bs_pred)
            bootstrap_scores.append(score)

        alpha = 1.0 - confidence_level
        lower_percentile = (alpha / 2.0) * 100.0
        upper_percentile = (1.0 - (alpha / 2.0)) * 100.0

        ci_lower = float(np.percentile(bootstrap_scores, lower_percentile))
        ci_upper = float(np.percentile(bootstrap_scores, upper_percentile))

        return {
            "point_estimate": round(point_est, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "confidence_level": confidence_level,
            "n_bootstraps": n_bootstraps
        }

    @staticmethod
    def per_class_agreement(ratings_matrix: np.ndarray) -> Dict[str, float]:
        """
        Computes proportion of unanimous agreement per category.
        """
        n_subjects, n_categories = ratings_matrix.shape
        m = np.sum(ratings_matrix, axis=1)[0]
        
        per_class = {}
        for c_idx, label in enumerate(["LOW", "MEDIUM", "HIGH"]):
            if c_idx < n_categories:
                # Assets where this category received majority (> 50%)
                majority_mask = ratings_matrix[:, c_idx] > (m / 2.0)
                if np.sum(majority_mask) > 0:
                    avg_agreement = np.mean(ratings_matrix[majority_mask, c_idx] / m)
                    per_class[label] = round(float(avg_agreement), 4)
                else:
                    per_class[label] = 0.0

        return per_class

