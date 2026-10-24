import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from .expert_validation import ExpertLabelClass


class AgreementMetrics:
    LABEL_ORDER = [ExpertLabelClass.LOW, ExpertLabelClass.MEDIUM, ExpertLabelClass.HIGH]

    @staticmethod
    def _encode_labels(labels: List[ExpertLabelClass]) -> List[int]:
        m = {ExpertLabelClass.LOW: 0, ExpertLabelClass.MEDIUM: 1, ExpertLabelClass.HIGH: 2}
        return [m[l] for l in labels if l in m]

    @staticmethod
    def cohens_kappa(
        y1: List[ExpertLabelClass],
        y2: List[ExpertLabelClass],
        weights: Optional[str] = "quadratic",
        bootstrap_ci: bool = False,
        n_bootstraps: int = 1000,
        seed: int = 42
    ) -> Dict[str, Any]:
        """Calculates Weighted Cohen's Kappa for two raters with optional bootstrap confidence interval."""
        valid_pairs = [(l1, l2) for l1, l2 in zip(y1, y2) if l1 != ExpertLabelClass.UNKNOWN and l2 != ExpertLabelClass.UNKNOWN]

        if len(valid_pairs) < 2:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient overlapping valid labels to compute Cohen's kappa (N < 2)."
            }

        enc1 = [AgreementMetrics.LABEL_ORDER.index(p[0]) for p in valid_pairs]
        enc2 = [AgreementMetrics.LABEL_ORDER.index(p[1]) for p in valid_pairs]

        # Check for zero variance
        if len(set(enc1)) <= 1 and len(set(enc2)) <= 1 and enc1[0] == enc2[0]:
            return {
                "status": "COMPUTED",
                "statistic": 1.0,
                "weights": weights,
                "comparable_pairs": len(valid_pairs),
                "bootstrap_ci_95": [1.0, 1.0] if bootstrap_ci else None
            }

        score = float(cohen_kappa_score(enc1, enc2, weights=weights))

        ci = None
        if bootstrap_ci and len(valid_pairs) >= 5:
            rng = np.random.default_rng(seed)
            boot_scores = []
            n_pairs = len(valid_pairs)
            for _ in range(n_bootstraps):
                idx = rng.choice(n_pairs, size=n_pairs, replace=True)
                b_enc1 = [enc1[i] for i in idx]
                b_enc2 = [enc2[i] for i in idx]
                if len(set(b_enc1)) <= 1 and len(set(b_enc2)) <= 1:
                    b_score = 1.0 if b_enc1[0] == b_enc2[0] else 0.0
                else:
                    b_score = float(cohen_kappa_score(b_enc1, b_enc2, weights=weights))
                boot_scores.append(b_score)
            ci = [
                round(float(np.percentile(boot_scores, 2.5)), 4),
                round(float(np.percentile(boot_scores, 97.5)), 4)
            ]

        return {
            "status": "COMPUTED",
            "statistic": round(score, 4),
            "weights": weights,
            "comparable_pairs": len(valid_pairs),
            "bootstrap_ci_95": ci
        }

    @staticmethod
    def fleiss_kappa(ratings_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Calculates Fleiss' kappa for multiple raters on a fixed set of items.
        ratings_matrix: (num_assets x num_categories) array containing counts of ratings.
        """
        if ratings_matrix.size == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Empty ratings matrix."
            }

        n_assets, n_cat = ratings_matrix.shape
        if n_assets == 0 or n_cat == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient raters or categories."
            }

        if np.any(ratings_matrix < 0):
            raise ValueError("Ratings matrix cannot contain negative counts.")

        raters_per_item = np.sum(ratings_matrix, axis=1)
        if not np.all(raters_per_item == raters_per_item[0]):
            raise ValueError("Number of raters per item must be equal across all items.")

        n_raters = raters_per_item[0]

        if n_raters <= 1:
            return {
                "status": "NOT_IMPLEMENTED",
                "statistic": None,
                "message": "Fleiss kappa requires at least 2 raters."
            }

        N = n_assets
        n = n_raters

        P_i = np.sum(ratings_matrix * (ratings_matrix - 1), axis=1) / (n * (n - 1))
        P_bar = np.mean(P_i)

        p_j = np.sum(ratings_matrix, axis=0) / (N * n)
        P_e_bar = np.sum(p_j ** 2)

        if P_e_bar == 1.0:
            return {
                "status": "COMPUTED",
                "statistic": 1.0
            }

        kappa = (P_bar - P_e_bar) / (1 - P_e_bar)

        return {
            "status": "COMPUTED",
            "statistic": round(float(kappa), 4)
        }

    @staticmethod
    def krippendorff_alpha(
        reliability_data: np.ndarray,
        level: str = "ordinal"
    ) -> Dict[str, Any]:
        """
        Computes Krippendorff's alpha for arbitrary number of annotators and missing data.
        reliability_data: shape (m_annotators, n_items). Missing ratings must be represented as np.nan.
        level: 'nominal' or 'ordinal'.
        """
        data = np.asarray(reliability_data, dtype=float)
        m_raters, n_items = data.shape

        if m_raters < 2 or n_items == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "At least 2 annotators and 1 item required."
            }

        # Filter items with at least 2 non-nan ratings
        valid_items_mask = np.sum(~np.isnan(data), axis=0) >= 2
        filtered_data = data[:, valid_items_mask]

        if filtered_data.shape[1] == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "No items have 2 or more ratings."
            }

        # Unique values across non-nan entries
        valid_values = filtered_data[~np.isnan(filtered_data)]
        unique_vals = np.unique(valid_values)
        if len(unique_vals) <= 1:
            return {
                "status": "COMPUTED",
                "statistic": 1.0,
                "level": level,
                "evaluated_items": int(filtered_data.shape[1]),
                "total_ratings": int(len(valid_values))
            }

        # Build coincidence matrix
        v_map = {val: i for i, val in enumerate(unique_vals)}
        K = len(unique_vals)
        coincidence = np.zeros((K, K), dtype=float)

        for col in range(filtered_data.shape[1]):
            col_vals = filtered_data[:, col]
            col_non_nan = col_vals[~np.isnan(col_vals)]
            m_u = len(col_non_nan)
            if m_u < 2:
                continue
            for r1 in range(m_u):
                for r2 in range(m_u):
                    if r1 != r2:
                        j_idx = v_map[col_non_nan[r1]]
                        k_idx = v_map[col_non_nan[r2]]
                        coincidence[j_idx, k_idx] += 1.0 / (m_u - 1)

        # Marginals
        n_c = np.sum(coincidence, axis=1)
        total_n = np.sum(n_c)

        if total_n <= 1:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "message": "Insufficient pairable ratings."
            }

        # Distance metric matrix delta^2(c, k)
        delta_sq = np.zeros((K, K), dtype=float)
        if level == "nominal":
            for j in range(K):
                for k in range(K):
                    delta_sq[j, k] = 0.0 if j == k else 1.0
        elif level == "ordinal":
            # Ordinal metric per Krippendorff (2011)
            # delta^2(c, k) = ( sum_{g=c}^k n_g - (n_c + n_k)/2 )^2
            for j in range(K):
                for k in range(K):
                    if j == k:
                        delta_sq[j, k] = 0.0
                    else:
                        start, end = min(j, k), max(j, k)
                        sum_between = np.sum(n_c[start : end + 1]) - (n_c[start] + n_c[end]) / 2.0
                        delta_sq[j, k] = float(sum_between ** 2)
        else:
            raise ValueError(f"Unsupported measurement level: {level}")

        # Observed disagreement D_o and expected disagreement D_e
        D_o = np.sum(coincidence * delta_sq)
        D_e = np.sum(np.outer(n_c, n_c) * delta_sq) / (total_n - 1)

        if D_e == 0.0:
            alpha = 1.0
        else:
            alpha = 1.0 - (D_o / D_e)

        return {
            "status": "COMPUTED",
            "statistic": round(float(alpha), 4),
            "level": level,
            "evaluated_items": int(filtered_data.shape[1]),
            "total_ratings": int(len(valid_values)),
            "unique_categories": [float(x) for x in unique_vals]
        }

    @staticmethod
    def per_class_agreement(
        y1: List[ExpertLabelClass],
        y2: List[ExpertLabelClass]
    ) -> Dict[str, Any]:
        """Calculates per-class agreement metrics, confusion matrix, and class-specific F1/Dice concordance."""
        valid_pairs = [(l1, l2) for l1, l2 in zip(y1, y2) if l1 != ExpertLabelClass.UNKNOWN and l2 != ExpertLabelClass.UNKNOWN]

        classes = [ExpertLabelClass.LOW.value, ExpertLabelClass.MEDIUM.value, ExpertLabelClass.HIGH.value]
        if len(valid_pairs) == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "confusion_matrix": None,
                "per_class_f1": None
            }

        y1_str = [p[0].value for p in valid_pairs]
        y2_str = [p[1].value for p in valid_pairs]

        cm = confusion_matrix(y1_str, y2_str, labels=classes)

        per_class_f1 = {}
        for idx, c in enumerate(classes):
            tp = cm[idx, idx]
            fp = np.sum(cm[:, idx]) - tp
            fn = np.sum(cm[idx, :]) - tp
            denom = 2 * tp + fp + fn
            f1 = (2.0 * tp / denom) if denom > 0 else 0.0
            per_class_f1[c] = round(float(f1), 4)

        return {
            "status": "COMPUTED",
            "classes": classes,
            "confusion_matrix": cm.tolist(),
            "per_class_f1": per_class_f1,
            "overall_accuracy": round(float(np.trace(cm) / np.sum(cm)), 4) if np.sum(cm) > 0 else 0.0
        }
