"""
Evaluation Script for Experimental Heuristic V2 Ablation Study.

Runs Leave-One-Repository-Out (LORO) cross-validation across the 7 benchmark repositories
in the expert validation corpus. Generates comprehensive ablation comparisons between
Production Baseline V1 and Experimental Heuristic V2 configurations.

Outputs:
  - backend/dataset/artifacts/heuristic_v2_experiment_results.json
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
from sklearn.metrics import f1_score, confusion_matrix, cohen_kappa_score, precision_recall_fscore_support

# Path setup
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.risk.factors import FactorValue, RiskFactors
from src.risk.heuristic import calculate_heuristic_score as calculate_v1_score
from src.risk.experimental_heuristic import (
    ExperimentalHeuristicConfig,
    calculate_experimental_heuristic_score,
    propagate_graph_crypto_weakness,
    classify_score,
    bootstrap_metric_ci
)

LMAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
REV_LMAP = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
KEYS = [
    "data_sensitivity", "asset_criticality", "internet_exposure", 
    "crypto_weakness", "cve_risk", "library_centrality", "migration_difficulty"
]


def load_dataset_and_graphs():
    report_path = ROOT_DIR / "dataset" / "artifacts" / "expert_validation_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    audit = report["asset_adjudication_audit"]
    graphs = {
        g.stem: torch.load(g, weights_only=False)
        for g in (ROOT_DIR / "dataset" / "artifacts").glob("*.pt")
    }
    return audit, graphs


def evaluate_configuration(
    audit: List[Dict[str, Any]],
    graphs: Dict[str, Any],
    config: ExperimentalHeuristicConfig,
    use_loro_calibration: bool = False
) -> Dict[str, Any]:
    """
    Evaluates a specific experimental configuration using either fixed thresholds
    or strict Leave-One-Repository-Out (LORO) cross-validation.
    """
    # 1. Compute propagated weaknesses per graph if enabled
    propagated_by_repo = {}
    if config.enable_graph_weakness_propagation:
        for repo_name, g in graphs.items():
            propagated_by_repo[repo_name] = propagate_graph_crypto_weakness(g, config=config)

    # 2. Extract features and continuous scores for each asset
    dataset_records = []
    for a in audit:
        aid = a["canonical_asset_id"]
        repo = a["repository"]
        g = graphs.get(repo)
        if not g or aid not in g["file"].node_ids:
            continue
        
        f_idx = g["file"].node_ids.index(aid)
        x = g["file"].x[f_idx].clone()

        # Check if weakness was propagated
        if repo in propagated_by_repo and aid in propagated_by_repo[repo]:
            x[3] = propagated_by_repo[repo][aid]
            x[10] = 0.0  # Mark as observed

        # Reconstruct RiskFactors
        f_dict = {
            k: FactorValue(value=x[i].item() if x[i+7].item() == 0.0 else None, source="eval", confidence=1.0)
            for i, k in enumerate(KEYS)
        }
        rf = RiskFactors(**f_dict)
        res = calculate_experimental_heuristic_score(rf, config=config)
        
        dataset_records.append({
            "asset_id": aid,
            "repository": repo,
            "y_true": LMAP[a["consensus_label"]],
            "score": res.score,
            "raw_factors": {k: (x[i].item() if x[i+7].item() == 0.0 else None) for i, k in enumerate(KEYS)}
        })

    y_true = np.array([d["y_true"] for d in dataset_records])
    repos = sorted(list(set(d["repository"] for d in dataset_records)))
    y_pred = np.zeros(len(dataset_records), dtype=int)
    thresholds_by_repo = {}

    if not use_loro_calibration:
        # Fixed thresholds
        for idx, d in enumerate(dataset_records):
            y_pred[idx] = classify_score(
                d["score"],
                low_threshold=config.default_low_threshold,
                high_threshold=config.default_high_threshold
            )
        fitted_th_str = f"Fixed ({config.default_low_threshold:.2f}, {config.default_high_threshold:.2f})"
    else:
        # Strict LORO Cross-Validation
        for r_test in repos:
            train_idx = [i for i, d in enumerate(dataset_records) if d["repository"] != r_test]
            test_idx = [i for i, d in enumerate(dataset_records) if d["repository"] == r_test]
            
            train_scores = np.array([dataset_records[i]["score"] for i in train_idx])
            train_y = np.array([dataset_records[i]["y_true"] for i in train_idx])

            # Grid search strictly on training fold
            best_f1 = -1.0
            best_th = (config.default_low_threshold, config.default_high_threshold)
            for th_l in np.arange(0.12, 0.36, 0.02):
                for th_h in np.arange(th_l + 0.06, 0.64, 0.02):
                    p = np.where(train_scores < th_l, 0, np.where(train_scores < th_h, 1, 2))
                    f1 = f1_score(train_y, p, average="macro", zero_division=0)
                    if f1 > best_f1:
                        best_f1 = f1
                        best_th = (float(th_l), float(th_h))

            thresholds_by_repo[r_test] = (round(best_th[0], 2), round(best_th[1], 2))
            
            # Apply strictly to held-out test fold
            for idx in test_idx:
                sc = dataset_records[idx]["score"]
                y_pred[idx] = classify_score(sc, low_threshold=best_th[0], high_threshold=best_th[1])

        fitted_th_str = "LORO-Calibrated"

    # Compute metrics
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_kappa = cohen_kappa_score(y_true, y_pred, weights="linear")
    accuracy = float(np.mean(y_true == y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()
    
    ci = bootstrap_metric_ci(
        lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0),
        y_true.tolist(),
        y_pred.tolist(),
        n_bootstraps=1000,
        seed=42
    )

    prec, rec, f1, supp = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1, 2], zero_division=0)
    per_class = {
        "LOW": {"precision": round(float(prec[0]), 4), "recall": round(float(rec[0]), 4), "f1": round(float(f1[0]), 4), "support": int(supp[0])},
        "MEDIUM": {"precision": round(float(prec[1]), 4), "recall": round(float(rec[1]), 4), "f1": round(float(f1[1]), 4), "support": int(supp[1])},
        "HIGH": {"precision": round(float(prec[2]), 4), "recall": round(float(rec[2]), 4), "f1": round(float(f1[2]), 4), "support": int(supp[2])}
    }

    # Per-repository breakdown
    repo_breakdown = {}
    for r in repos:
        r_indices = [i for i, d in enumerate(dataset_records) if d["repository"] == r]
        if r_indices:
            r_yt = y_true[r_indices]
            r_yp = y_pred[r_indices]
            repo_breakdown[r] = {
                "sample_size": len(r_indices),
                "accuracy": round(float(np.mean(r_yt == r_yp)), 4),
                "macro_f1": round(float(f1_score(r_yt, r_yp, average="macro", zero_division=0)), 4),
                "fitted_thresholds": thresholds_by_repo.get(r, None)
            }

    return {
        "macro_f1": round(float(macro_f1), 4),
        "weighted_cohens_kappa": round(float(weighted_kappa), 4),
        "accuracy": round(float(accuracy), 4),
        "bootstrap_95ci": ci,
        "confusion_matrix": {
            "labels": ["LOW", "MEDIUM", "HIGH"],
            "matrix": cm
        },
        "per_class_metrics": per_class,
        "threshold_strategy": fitted_th_str,
        "thresholds_by_held_out_repo": thresholds_by_repo,
        "per_repository_performance": repo_breakdown
    }


def main():
    print("=================================================================")
    print("      AgileGraph Experimental Heuristic V2 Ablation Study        ")
    print("=================================================================")
    audit, graphs = load_dataset_and_graphs()
    print(f"Loaded {len(audit)} audited assets across {len(graphs)} repository graphs.\n")

    experiments = {
        "1_Baseline_V1": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v1.0",
                enable_data_aware_thresholds=False,
                enable_graph_weakness_propagation=False,
                enable_pqc_dominance_floor=False
            ),
            "use_loro": False,
            "description": "Production Baseline V1 (Fixed 0.30/0.60 thresholds, no weakness propagation)"
        },
        "2_V2_Threshold_Calibration_Only": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v2.0-threshold-only",
                enable_data_aware_thresholds=True,
                enable_graph_weakness_propagation=False,
                enable_pqc_dominance_floor=False
            ),
            "use_loro": True,
            "description": "V2 Strategy 1 Only: Data-Aware Threshold Calibration via LORO CV"
        },
        "3_V2_Graph_Propagation_Only": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v2.0-propagation-only",
                enable_data_aware_thresholds=False,
                enable_graph_weakness_propagation=True,
                enable_pqc_dominance_floor=False,
                attenuation_factor=0.55
            ),
            "use_loro": False,
            "description": "V2 Strategy 2 Only: Graph Weakness Propagation Only (Fixed 0.30/0.60 thresholds)"
        },
        "4_V2_Combined_Calibrated_and_Propagated": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v2.0-combined",
                enable_data_aware_thresholds=True,
                enable_graph_weakness_propagation=True,
                enable_pqc_dominance_floor=False,
                attenuation_factor=0.55
            ),
            "use_loro": True,
            "description": "V2 Combined: Threshold Calibration + Graph Weakness Propagation via LORO CV"
        },
        "5_Strategy_3_PQC_Dominance_Floor_Alone": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v2.0-pqc-floor-alone",
                enable_data_aware_thresholds=False,
                enable_graph_weakness_propagation=False,
                enable_pqc_dominance_floor=True,
                pqc_floor_factor=0.70
            ),
            "use_loro": False,
            "description": "Strategy 3: Non-Linear PQC Dominance Floor Alone (Fixed 0.30/0.60 thresholds)"
        },
        "6_V2_Full_Combined_with_PQC_Floor": {
            "config": ExperimentalHeuristicConfig(
                version_id="heuristic-v2.0-full-suite",
                enable_data_aware_thresholds=True,
                enable_graph_weakness_propagation=True,
                enable_pqc_dominance_floor=True,
                attenuation_factor=0.55,
                pqc_floor_factor=0.70
            ),
            "use_loro": True,
            "description": "V2 Full Combined: Calibration + Propagation + PQC Dominance Floor via LORO CV"
        }
    }

    results = {}
    for exp_key, exp_info in experiments.items():
        print(f"Executing [{exp_key}]: {exp_info['description']}...")
        res = evaluate_configuration(
            audit=audit,
            graphs=graphs,
            config=exp_info["config"],
            use_loro_calibration=exp_info["use_loro"]
        )
        res["description"] = exp_info["description"]
        results[exp_key] = res
        print(f"  -> Macro-F1: {res['macro_f1']:.4f} (95% CI: [{res['bootstrap_95ci']['ci_lower']:.4f}, {res['bootstrap_95ci']['ci_upper']:.4f}])")
        print(f"  -> Weighted Kappa: {res['weighted_cohens_kappa']:.4f}")
        print(f"  -> Accuracy: {res['accuracy'] * 100:.2f}%\n")

    # Save to json
    out_path = ROOT_DIR / "dataset" / "artifacts" / "heuristic_v2_experiment_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"All ablation experiment results saved to:\n  {out_path}")


if __name__ == "__main__":
    main()

