import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class EvaluationMetrics:
    @staticmethod
    def calculate_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
        """Calculates macro-F1, precision, recall, and accuracy."""
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "macro_f1": None,
                "macro_precision": None,
                "macro_recall": None,
                "accuracy": None
            }
            
        classes = np.unique(np.concatenate((y_true, y_pred)))
        metrics = {}
        
        macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
        
        for c in classes:
            tp = np.sum((y_pred == c) & (y_true == c))
            fp = np.sum((y_pred == c) & (y_true != c))
            fn = np.sum((y_pred != c) & (y_true == c))
            
            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
            
            metrics[f"class_{c}_precision"] = p
            metrics[f"class_{c}_recall"] = r
            metrics[f"class_{c}_f1"] = f1
            
            macro_p += p
            macro_r += r
            macro_f1 += f1
            
        n_classes = len(classes) if len(classes) > 0 else 1
        metrics["status"] = "COMPUTED"
        metrics["macro_precision"] = macro_p / n_classes
        metrics["macro_recall"] = macro_r / n_classes
        metrics["macro_f1"] = macro_f1 / n_classes
        metrics["accuracy"] = np.sum(y_true == y_pred) / len(y_true) if len(y_true) > 0 else 0.0
        
        return metrics

    @staticmethod
    def bootstrap_ci(y_true: np.ndarray, y_pred: np.ndarray, n_bootstraps: int = 1000, alpha: float = 0.05) -> Dict[str, Any]:
        """Calculates bootstrap confidence interval for accuracy."""
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "confidence_interval": None
            }
        
        from sklearn.metrics import accuracy_score
        bootstrapped_scores = []
        rng = np.random.RandomState(42)
        n = len(y_true)
        for _ in range(n_bootstraps):
            indices = rng.randint(0, n, n)
            score = accuracy_score(y_true[indices], y_pred[indices])
            bootstrapped_scores.append(score)
            
        lower = np.percentile(bootstrapped_scores, (alpha / 2) * 100)
        upper = np.percentile(bootstrapped_scores, (1 - alpha / 2) * 100)
        
        return {
            "status": "COMPUTED",
            "confidence_interval": (float(lower), float(upper))
        }

    @staticmethod
    def paired_permutation_test(y_true: np.ndarray, y_pred_a: np.ndarray, y_pred_b: np.ndarray, n_permutations: int = 1000) -> Dict[str, Any]:
        """Calculates paired permutation test for difference in accuracy."""
        if len(y_true) == 0 or len(y_pred_a) == 0 or len(y_pred_b) == 0:
            return {
                "status": "PENDING_EXPERT_LABELS",
                "statistic": None,
                "p_value": None
            }
        
        from sklearn.metrics import accuracy_score
        acc_a = accuracy_score(y_true, y_pred_a)
        acc_b = accuracy_score(y_true, y_pred_b)
        obs_diff = abs(acc_a - acc_b)
        
        rng = np.random.RandomState(42)
        count = 0
        n = len(y_true)
        
        for _ in range(n_permutations):
            swap = rng.binomial(1, 0.5, n)
            perm_a = np.where(swap, y_pred_b, y_pred_a)
            perm_b = np.where(swap, y_pred_a, y_pred_b)
            diff = abs(accuracy_score(y_true, perm_a) - accuracy_score(y_true, perm_b))
            if diff >= obs_diff:
                count += 1
                
        p_value = count / n_permutations
        return {
            "status": "COMPUTED",
            "statistic": float(obs_diff),
            "p_value": float(p_value)
        }
