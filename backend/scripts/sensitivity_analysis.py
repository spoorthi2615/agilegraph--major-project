"""
AgileGraph Heuristic Sensitivity Analysis Script.

Perturbs heuristic factor weights by +/-10% and +/-20% with proportional simplex renormalization.
Evaluates ranking robustness (Spearman rho, Kendall tau), score shift, and queue overlap (Top 10/20)
under both RENORMALIZE and CONSERVATIVE missing-data policies.

Outputs:
  - dataset/sensitivity/sensitivity_summary.json
  - dataset/sensitivity/sensitivity_table.csv
  - dataset/sensitivity/sensitivity_tornado.png

DISCLAIMER:
  Stability != Correctness: Robustness of rankings to weight perturbations demonstrates
  mathematical stability under parametric jitter, but does NOT establish empirical validity
  or predictive accuracy of the risk scores.
"""

import os
import sys
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.risk.weights import HeuristicWeights
from src.risk.factors import RiskFactors, FactorValue
from src.risk.score import MissingDataPolicy
from src.risk.sensitivity_analysis import SensitivityEngine, SensitivityReport
from src.pipeline.runner import run_pipeline

OUTPUT_DIR = "dataset/sensitivity"
CORPUS_ROOT = "dataset/corpus"

BENCHMARK_REPOS = [
    "python_itsdangerous", "python_bcrypt", "python_cryptography",
    "java_java_jwt", "java_jjwt", "go_jwt", "go_jwt_go", "go_crypto"
]

DISCLAIMER = (
    "Stability != Correctness: Robustness of rankings to weight perturbations demonstrates "
    "mathematical stability under parametric jitter, but does NOT establish empirical validity "
    "or predictive accuracy of the risk scores."
)


def load_corpus_asset_factors() -> Dict[str, Dict[str, RiskFactors]]:
    """
    Scans corpus repositories to extract concrete factor profiles per asset.
    Returns: {repo_id: {asset_id: RiskFactors}}
    """
    repo_factors = {}
    for repo_id in BENCHMARK_REPOS:
        repo_dir = os.path.join(CORPUS_ROOT, repo_id)
        if not os.path.exists(repo_dir):
            continue
        try:
            res = run_pipeline(repo_dir, repo_id, allowed_root=repo_dir)
            factors_map = {}
            for s in res.get("scores", []):
                aid = s["asset_id"]
                raw_factors = s.get("factors", {})
                kwargs = {}
                for fname in SensitivityEngine.FACTORS:
                    fdict = raw_factors.get(fname, {})
                    kwargs[fname] = FactorValue(
                        value=fdict.get("value"),
                        source=fdict.get("source", "scanner"),
                        confidence=fdict.get("confidence", 1.0)
                    )
                factors_map[aid] = RiskFactors(**kwargs)
            if factors_map:
                repo_factors[repo_id] = factors_map
        except Exception as e:
            print(f"Note: Error collecting factors from {repo_id}: {e}")

    # Fallback to synthetic benchmark assets if corpus not checked out
    if not repo_factors:
        print("Corpus not available; generating representative benchmark asset distribution...")
        dummy = {}
        for i in range(50):
            aid = f"synthetic_asset_{i:02d}"
            kwargs = {}
            for fname in SensitivityEngine.FACTORS:
                # Stochastic varied factor values
                val = float(np.clip(np.random.beta(2, 5) if i % 2 == 0 else np.random.beta(5, 2), 0.0, 1.0))
                kwargs[fname] = FactorValue(value=round(val, 2), source="synthetic", confidence=1.0)
            dummy[aid] = RiskFactors(**kwargs)
        repo_factors["synthetic_benchmark"] = dummy

    return repo_factors


def run_sensitivity_analysis():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    baseline_weights = HeuristicWeights.from_config()

    print(f"Running Heuristic Sensitivity Analysis across 7 factors (Baseline weights: {baseline_weights.model_dump()})...")
    repo_factors = load_corpus_asset_factors()

    results_summary = {
        "metadata": {
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "baseline_weights": baseline_weights.model_dump(),
            "perturbation_deltas": [-0.20, -0.10, 0.10, 0.20],
            "policies_tested": ["RENORMALIZE", "CONSERVATIVE"],
            "disclaimer": DISCLAIMER
        },
        "per_repository": {},
        "corpus_aggregate": {}
    }

    csv_rows = []

    # Run per repository and aggregate
    all_corpus_factors = {}
    for repo_id, assets in repo_factors.items():
        all_corpus_factors.update(assets)
        results_summary["per_repository"][repo_id] = {}

        for policy in [MissingDataPolicy.RENORMALIZE, MissingDataPolicy.CONSERVATIVE]:
            report = SensitivityEngine.run_sensitivity_study(
                baseline=baseline_weights,
                asset_factors=assets,
                deltas=[-0.20, -0.10, 0.10, 0.20],
                policy=policy
            )
            results_summary["per_repository"][repo_id][policy.value] = report.model_dump()

            for r in report.results:
                csv_rows.append({
                    "repository": repo_id,
                    "policy": policy.value,
                    "factor_perturbed": r.factor_perturbed,
                    "delta_percent": f"{r.delta_percent:+.0%}",
                    "mean_abs_score_change": r.mean_absolute_score_change,
                    "max_abs_score_change": r.max_absolute_score_change,
                    "spearman_rho": r.spearman_rank_correlation,
                    "kendall_tau": r.kendall_tau,
                    "top_10_overlap": r.top_10_overlap_ratio,
                    "top_20_overlap": r.top_20_overlap_ratio,
                })

    # Corpus aggregate
    for policy in [MissingDataPolicy.RENORMALIZE, MissingDataPolicy.CONSERVATIVE]:
        agg_report = SensitivityEngine.run_sensitivity_study(
            baseline=baseline_weights,
            asset_factors=all_corpus_factors,
            deltas=[-0.20, -0.10, 0.10, 0.20],
            policy=policy
        )
        results_summary["corpus_aggregate"][policy.value] = agg_report.model_dump()

        for r in agg_report.results:
            csv_rows.append({
                "repository": "__CORPUS_AGGREGATE__",
                "policy": policy.value,
                "factor_perturbed": r.factor_perturbed,
                "delta_percent": f"{r.delta_percent:+.0%}",
                "mean_abs_score_change": r.mean_absolute_score_change,
                "max_abs_score_change": r.max_absolute_score_change,
                "spearman_rho": r.spearman_rank_correlation,
                "kendall_tau": r.kendall_tau,
                "top_10_overlap": r.top_10_overlap_ratio,
                "top_20_overlap": r.top_20_overlap_ratio,
            })

    # Save JSON summary
    json_path = os.path.join(OUTPUT_DIR, "sensitivity_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    # Save CSV table
    csv_path = os.path.join(OUTPUT_DIR, "sensitivity_table.csv")
    fieldnames = [
        "repository", "policy", "factor_perturbed", "delta_percent",
        "mean_abs_score_change", "max_abs_score_change",
        "spearman_rho", "kendall_tau", "top_10_overlap", "top_20_overlap"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # Generate Tornado / Sensitivity Plot
    plot_path = os.path.join(OUTPUT_DIR, "sensitivity_tornado.png")
    generate_sensitivity_plot(results_summary["corpus_aggregate"]["RENORMALIZE"], plot_path)

    print("\nSensitivity Analysis Complete:")
    print(f"  JSON summary: {json_path}")
    print(f"  CSV table:    {csv_path}")
    print(f"  Plot:         {plot_path}")


def generate_sensitivity_plot(report_dict: Dict[str, Any], out_path: str):
    """
    Renders horizontal bar chart (Tornado-style) showing mean score sensitivity per factor under +/-20% perturbations.
    """
    results = report_dict.get("results", [])
    factors = SensitivityEngine.FACTORS
    
    pos_20 = {r["factor_perturbed"]: r["mean_absolute_score_change"] for r in results if r["delta_percent"] == 0.20}
    neg_20 = {r["factor_perturbed"]: r["mean_absolute_score_change"] for r in results if r["delta_percent"] == -0.20}

    y_pos = np.arange(len(factors))
    pos_vals = [pos_20.get(f, 0.0) for f in factors]
    neg_vals = [neg_20.get(f, 0.0) for f in factors]

    plt.figure(figsize=(10, 6))
    bar_width = 0.35

    plt.barh(y_pos - bar_width/2, pos_vals, bar_width, label="+20% Perturbation", color="#3b82f6")
    plt.barh(y_pos + bar_width/2, neg_vals, bar_width, label="-20% Perturbation", color="#93c5fd")

    plt.yticks(y_pos, [f.replace("_", " ").title() for f in factors])
    plt.xlabel("Mean Absolute Score Change")
    plt.title("AgileGraph Factor Sensitivity Analysis (Corpus Aggregate, Renormalize Policy)")
    plt.legend(loc="lower right")
    plt.grid(axis="x", linestyle="--", alpha=0.5)

    # Add disclaimer box at bottom
    plt.figtext(
        0.5, 0.01,
        "Disclaimer: Stability != Correctness (Robustness confirms mathematical stability, not predictive truth)",
        wrap=True, horizontalalignment='center', fontsize=8, color="#6b7280"
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(out_path, dpi=200)
    plt.close()


if __name__ == "__main__":
    run_sensitivity_analysis()
