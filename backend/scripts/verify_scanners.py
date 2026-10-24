"""
AgileGraph Scanner Ground-Truth Verification Tooling.

Runs static scanners against the curated multi-language reference benchmark set,
computing empirical Precision, Recall, and F1 score against consensus labels.

Enforces empirical integrity: Strictly refuses to report metrics if any sample
contains an empty or unadjudicated consensus label.
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.common.enums import AssetType

REFERENCE_SET_PATH = "dataset/reference_set/reference_samples.json"


def verify_scanners(ref_path: str = REFERENCE_SET_PATH) -> Dict[str, Any]:
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference set not found: {ref_path}")

    with open(ref_path, "r", encoding="utf-8") as f:
        samples: List[Dict[str, Any]] = json.load(f)

    if not samples:
        raise ValueError("Reference set is empty! Refusing to report metrics.")

    # 1. Validation check: Enforce non-empty consensus labels
    unlabeled_items = []
    for item in samples:
        c_label = item.get("consensus_label")
        if not c_label or str(c_label).strip() == "":
            unlabeled_items.append(item.get("item_id", "unknown"))

    if unlabeled_items:
        raise ValueError(
            f"Reference set contains unadjudicated or empty consensus labels "
            f"for {len(unlabeled_items)} items: {unlabeled_items}. "
            f"Verification REFUSES to compute metrics on incomplete ground truth."
        )

    # 2. Evaluation per language
    metrics_by_lang = {
        "PYTHON": {"TP": 0, "FP": 0, "FN": 0, "TN": 0},
        "JAVA":   {"TP": 0, "FP": 0, "FN": 0, "TN": 0},
        "GO":     {"TP": 0, "FP": 0, "FN": 0, "TN": 0},
    }

    item_results = []

    for item in samples:
        iid = item["item_id"]
        lang = item["language"].upper()
        code = item["code"]
        expected = item["consensus_label"]

        if lang == "PYTHON":
            findings = scan_python_code("ref_repo", "sample.py", code)
        elif lang == "JAVA":
            findings = scan_java_code("ref_repo", "Sample.java", code)
        elif lang == "GO":
            findings = scan_go_code("ref_repo", "sample.go", code)
        else:
            continue

        crypto_findings = [f for f in findings if f.asset_type == AssetType.CRYPTO_USAGE]
        has_detection = len(crypto_findings) > 0

        is_positive = (expected != "NEGATIVE")

        if is_positive and has_detection:
            metrics_by_lang[lang]["TP"] += 1
            verdict = "TP"
        elif not is_positive and has_detection:
            metrics_by_lang[lang]["FP"] += 1
            verdict = "FP"
        elif is_positive and not has_detection:
            metrics_by_lang[lang]["FN"] += 1
            verdict = "FN"
        else:
            metrics_by_lang[lang]["TN"] += 1
            verdict = "TN"

        item_results.append({
            "item_id": iid,
            "language": lang,
            "expected": expected,
            "detected_findings": len(crypto_findings),
            "verdict": verdict
        })

    # 3. Calculate Precision, Recall, F1
    summary = {}
    tot_tp, tot_fp, tot_fn, tot_tn = 0, 0, 0, 0

    for lang, counts in metrics_by_lang.items():
        tp = counts["TP"]
        fp = counts["FP"]
        fn = counts["FN"]
        tn = counts["TN"]
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn
        tot_tn += tn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        summary[lang] = {
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }

    overall_prec = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 1.0
    overall_rec = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 1.0
    overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0

    summary["OVERALL"] = {
        "TP": tot_tp, "FP": tot_fp, "FN": tot_fn, "TN": tot_tn,
        "precision": round(overall_prec, 4),
        "recall": round(overall_rec, 4),
        "f1_score": round(overall_f1, 4),
        "total_evaluated_samples": len(samples)
    }

    return {
        "summary": summary,
        "item_details": item_results
    }


def main():
    print("=" * 65)
    print(" AgileGraph Static Scanner Reference Set Verification")
    print("=" * 65)
    
    try:
        report = verify_scanners()
    except ValueError as e:
        print(f"\n[ERROR] Verification aborted: {e}")
        sys.exit(1)

    summary = report["summary"]
    print(f"\n{'Language':<10} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'TN':<4} | {'Precision':<9} | {'Recall':<8} | {'F1':<6}")
    print("-" * 65)
    for lang in ["PYTHON", "JAVA", "GO", "OVERALL"]:
        s = summary[lang]
        print(
            f"{lang:<10} | {s['TP']:<4} | {s['FP']:<4} | {s['FN']:<4} | {s['TN']:<4} | "
            f"{s['precision']:<9.4f} | {s['recall']:<8.4f} | {s['f1_score']:<6.4f}"
        )
    print("=" * 65)
    print("All reference benchmark samples verified successfully.")


if __name__ == "__main__":
    main()
