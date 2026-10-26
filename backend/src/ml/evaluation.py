import numpy as np
from typing import Dict, List, Tuple, Any, Optional

class EvaluationMetrics:
    @staticmethod
    def calculate_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, target_classes: Optional[List[int]] = None) -> Dict[str, Any]:
        """Calculates macro-F1, precision, recall, accuracy, balanced accuracy, and confusion matrix."""
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                "status": "NOT_APPLICABLE",
                "macro_f1": None,
                "macro_precision": None,
                "macro_recall": None,
                "accuracy": None,
                "balanced_accuracy": None,
                "confusion_matrix": None
            }
            
        classes = np.array(target_classes) if target_classes is not None else np.unique(np.concatenate((y_true, y_pred)))
        metrics = {}
        
        macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
        
        for c in classes:
            tp = int(np.sum((y_pred == c) & (y_true == c)))
            fp = int(np.sum((y_pred == c) & (y_true != c)))
            fn = int(np.sum((y_pred != c) & (y_true == c)))
            
            p = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            r = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = float(2 * (p * r) / (p + r)) if (p + r) > 0 else 0.0
            
            metrics[f"class_{c}_precision"] = p
            metrics[f"class_{c}_recall"] = r
            metrics[f"class_{c}_f1"] = f1
            
            macro_p += p
            macro_r += r
            macro_f1 += f1
            
        n_classes = len(classes) if len(classes) > 0 else 1
        metrics["status"] = "COMPUTED"
        metrics["macro_precision"] = float(macro_p / n_classes)
        metrics["macro_recall"] = float(macro_r / n_classes)
        metrics["macro_f1"] = float(macro_f1 / n_classes)
        
        # Standard balanced accuracy averages recall strictly across classes present in ground truth
        # to prevent artificial deflation when a class has zero support in a fold.
        from sklearn.metrics import balanced_accuracy_score
        try:
            metrics["balanced_accuracy"] = float(balanced_accuracy_score(y_true, y_pred))
        except Exception:
            present_classes = [c for c in classes if np.sum(y_true == c) > 0]
            if present_classes:
                metrics["balanced_accuracy"] = float(np.mean([metrics[f"class_{c}_recall"] for c in present_classes]))
            else:
                metrics["balanced_accuracy"] = 0.0

        metrics["support_per_class"] = {int(c): int(np.sum(y_true == c)) for c in classes}
        metrics["accuracy"] = float(np.sum(y_true == y_pred) / len(y_true)) if len(y_true) > 0 else 0.0
        
        cm = []
        for i in classes:
            row = []
            for j in classes:
                row.append(int(np.sum((y_true == i) & (y_pred == j))))
            cm.append(row)
        metrics["confusion_matrix"] = cm
        metrics["classes"] = [int(c) for c in classes]
        
        return metrics

    @staticmethod
    def bootstrap_ci(y_true: np.ndarray, y_pred: np.ndarray, n_bootstraps: int = 1000, alpha: float = 0.05) -> Dict[str, Any]:
        """Calculates bootstrap confidence interval for accuracy."""
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                "status": "NOT_APPLICABLE",
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
                "status": "NOT_APPLICABLE",
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
                
        p_value = (count + 1) / (n_permutations + 1)
        return {
            "status": "COMPUTED",
            "statistic": float(obs_diff),
            "p_value": float(p_value)
        }
