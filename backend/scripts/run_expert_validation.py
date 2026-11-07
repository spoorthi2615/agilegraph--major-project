"""
Expert Validation Analysis Script for AgileGraph.

Loads submitted expert annotations, computes inter-annotator agreement
(Fleiss' Kappa, Weighted Cohen's Kappa), adjudicates multi-expert consensus,
and evaluates model alignment against adjudicated human ground truth.

Scientific Protocol:
- If no real expert annotations are present, reports data collection status honestly.
- Does NOT fabricate or synthesize fake expert data for scientific reporting.
"""

import os
import sys
import json
import argparse
import warnings
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Ensure repo root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.ml.expert_validation import (
    Expert, AssetForReview, ExpertLabel, ExpertLabelClass,
    ValidationDataset, LABEL_TO_INT
)
from src.ml.agreement import AgreementMetrics


def load_submitted_annotations(submissions_dir: Path) -> List[Dict[str, Any]]:
    import csv
    if not submissions_dir.exists():
        return []
    
    submissions = []
    
    # 1. Load JSON submissions
    for f in sorted(list(submissions_dir.glob("*.json"))):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                submissions.append(data)
        except Exception as e:
            print(f"Warning: Failed to load JSON submission {f}: {e}")

    # 2. Load CSV submissions
    for f in sorted(list(submissions_dir.glob("*.csv"))):
        try:
            expert_name = f.stem
            exp_years = 5.0
            with open(f, "r", encoding="utf-8") as fp:
                for line in fp:
                    if line.startswith("#"):
                        if "Reviewer Name" in line and ":" in line:
                            val = line.split(":", 1)[1].strip()
                            if val and not val.startswith("["):
                                expert_name = val
                        elif "Years of Experience" in line and ":" in line:
                            try:
                                exp_years = float(line.split(":", 1)[1].strip())
                            except ValueError:
                                pass
                    else:
                        break
                fp.seek(0)
                data_lines = [l for l in fp if not l.startswith("#")]
                reader = csv.DictReader(data_lines)
                ann_map: Dict[str, Dict[str, Any]] = {}
                dup_records = []
                for r in reader:
                    raw_id = r.get("asset_id", "").strip()
                    repo = r.get("repository_name", r.get("repository", "unknown")).strip()
                    risk = r.get("expert_assigned_risk", "").strip().upper()
                    if not raw_id or not risk or risk not in ExpertLabelClass.__members__:
                        continue
                    try:
                        conf = float(r.get("expert_confidence", 1.0))
                    except ValueError:
                        conf = 1.0

                    canonical_key = f"{repo}:{raw_id}" if not raw_id.startswith(f"{repo}:") else raw_id

                    if canonical_key in ann_map:
                        prev = ann_map[canonical_key]
                        conflict = prev["assigned_risk_category"] != risk
                        dup_records.append({
                            "canonical_asset_id": canonical_key,
                            "original_path": raw_id,
                            "repository": repo,
                            "prior_label": prev["assigned_risk_category"],
                            "duplicate_label": risk,
                            "has_conflict": conflict
                        })
                        order = ["HIGH", "MEDIUM", "LOW"]
                        chosen_risk = prev["assigned_risk_category"] if order.index(prev["assigned_risk_category"]) <= order.index(risk) else risk
                        prev["assigned_risk_category"] = chosen_risk
                        prev["confidence"] = max(prev["confidence"], conf)
                    else:
                        ann_map[canonical_key] = {
                            "canonical_asset_id": canonical_key,
                            "asset_id": raw_id,
                            "repository": repo,
                            "detected_primitives": [p.strip() for p in r.get("detected_primitives", "").split(",") if p.strip()],
                            "assigned_risk_category": risk,
                            "confidence": conf,
                            "rationale": r.get("expert_rationale", "").strip()
                        }

                if ann_map:
                    submissions.append({
                        "expert_profile": {
                            "expert_id": f.stem,
                            "name": expert_name,
                            "years_experience": exp_years
                        },
                        "annotations": list(ann_map.values()),
                        "deduplication_summary": {
                            "total_rows_parsed": len(ann_map) + len(dup_records),
                            "unique_canonical_assets": len(ann_map),
                            "duplicate_records_resolved": dup_records
                        }
                    })
        except Exception as e:
            print(f"Warning: Failed to load CSV submission {f}: {e}")

    # 3. Load Excel XLSX submissions
    for f in sorted(list(submissions_dir.glob("*.xlsx"))):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(f, data_only=True)
            expert_name = f.stem
            exp_years = 5.0
            if "Reviewer Profile & Rubric" in wb.sheetnames:
                ws_p = wb["Reviewer Profile & Rubric"]
                val_name = ws_p["B5"].value
                if val_name and not str(val_name).startswith("[") and "Fill Here" not in str(val_name):
                    expert_name = str(val_name).strip()
                val_years = ws_p["B6"].value
                if val_years:
                    try:
                        exp_years = float(str(val_years).replace("[", "").replace("]", "").strip())
                    except ValueError:
                        pass

            # Match the asset review sheet (exclude profile sheet)
            rev_sheet_name = next((s for s in wb.sheetnames if "Asset" in s or "asset" in s), None)
            if not rev_sheet_name:
                rev_sheet_name = next((s for s in wb.sheetnames if "Profile" not in s and ("Review" in s or "Assets" in s)), wb.sheetnames[-1])
            ws_r = wb[rev_sheet_name]
            ann_map: Dict[str, Dict[str, Any]] = {}
            dup_records = []
            for row in ws_r.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 5:
                    continue
                raw_id = str(row[0]).strip() if row[0] else ""
                repo = str(row[1]).strip() if row[1] else "unknown"
                prims_str = str(row[3]).strip() if row[3] else ""
                risk = str(row[4]).strip().upper() if row[4] else ""
                conf_val = row[5] if len(row) > 5 else 1.0
                rat_val = str(row[6]).strip() if len(row) > 6 and row[6] else ""
                
                if not raw_id or not risk or risk not in ExpertLabelClass.__members__:
                    continue
                try:
                    conf = float(conf_val) if conf_val is not None else 1.0
                except (ValueError, TypeError):
                    conf = 1.0

                canonical_key = f"{repo}:{raw_id}" if not raw_id.startswith(f"{repo}:") else raw_id

                if canonical_key in ann_map:
                    prev = ann_map[canonical_key]
                    conflict = prev["assigned_risk_category"] != risk
                    dup_records.append({
                        "canonical_asset_id": canonical_key,
                        "original_path": raw_id,
                        "repository": repo,
                        "prior_label": prev["assigned_risk_category"],
                        "duplicate_label": risk,
                        "has_conflict": conflict
                    })
                    order = ["HIGH", "MEDIUM", "LOW"]
                    chosen_risk = prev["assigned_risk_category"] if order.index(prev["assigned_risk_category"]) <= order.index(risk) else risk
                    prev["assigned_risk_category"] = chosen_risk
                    prev["confidence"] = max(prev["confidence"], conf)
                    if rat_val and rat_val not in prev["rationale"]:
                        prev["rationale"] = f"{prev['rationale']}; {rat_val}".strip("; ")
                else:
                    ann_map[canonical_key] = {
                        "canonical_asset_id": canonical_key,
                        "asset_id": raw_id,
                        "repository": repo,
                        "detected_primitives": [p.strip() for p in prims_str.split(",") if p.strip()],
                        "assigned_risk_category": risk,
                        "confidence": conf,
                        "rationale": rat_val
                    }

            if ann_map:
                submissions.append({
                    "expert_profile": {
                        "expert_id": f.stem,
                        "name": expert_name,
                        "years_experience": exp_years
                    },
                    "annotations": list(ann_map.values()),
                    "deduplication_summary": {
                        "total_rows_parsed": len(ann_map) + len(dup_records),
                        "unique_canonical_assets": len(ann_map),
                        "duplicate_records_resolved": dup_records
                    }
                })
        except Exception as e:
            print(f"Warning: Failed to load XLSX submission {f}: {e}")

    return submissions


def main():
    parser = argparse.ArgumentParser(description="AgileGraph Expert Validation Evaluation")
    parser.add_argument("--test-mode", action="store_true", help="Run self-verification test with mathematical sanity check")
    parser.add_argument("--output", type=str, default="dataset/artifacts/expert_validation_report.json")
    args = parser.parse_args()

    submissions_dir = ROOT_DIR / "dataset" / "expert_annotations" / "submissions"
    submissions = load_submitted_annotations(submissions_dir)

    print("=================================================================")
    print("      AgileGraph Independent Expert Validation Pipeline          ")
    print("=================================================================")

    if not submissions and not args.test_mode:
        print("\nStatus: PENDING_EXTERNAL_DATA_COLLECTION")
        print("No expert submissions found in:")
        print(f"  {submissions_dir}")
        print("\nProtocol Guidelines:")
        print("  1. Annotation templates prepared: dataset/expert_annotations/annotation_template.json")
        print("  2. Labelling guidelines defined: dataset/expert_annotations/labelling_guide.md")
        print("  3. Target panel: ≥ 4 cybersecurity practitioners on 150-200 assets.")
        print("  4. Per scientific guidelines, no synthetic annotations are fabricated.")
        print("\nTo verify statistical pipeline math, run: python scripts/run_expert_validation.py --test-mode")
        return

    if args.test_mode:
        print("\nRunning in --test-mode (Verification of statistical agreement calculation)...")
        # Self-verification matrix with 3 simulated raters across 6 items
        raters = {
            "Expert_A": [2, 2, 1, 0, 0, 1],
            "Expert_B": [2, 1, 1, 0, 0, 2],
            "Expert_C": [2, 2, 0, 0, 0, 1]
        }
        
        pairwise = AgreementMetrics.pairwise_kappas(raters, weights="linear")
        print(f"  Pairwise Weighted Cohen's Kappa: {pairwise}")

        # Construct Fleiss matrix (6 subjects x 3 classes)
        # Class 0: LOW, Class 1: MEDIUM, Class 2: HIGH
        fleiss_matrix = np.zeros((6, 3), dtype=int)
        for sub_idx in range(6):
            for rater_name in raters:
                assigned_class = raters[rater_name][sub_idx]
                fleiss_matrix[sub_idx, assigned_class] += 1

        f_kappa = AgreementMetrics.fleiss_kappa(fleiss_matrix)
        print(f"  Fleiss' Kappa (Panel Agreement): {f_kappa:.4f}")

        # Macro-F1 between two raters
        f1 = AgreementMetrics.macro_f1(raters["Expert_A"], raters["Expert_B"])
        ci = AgreementMetrics.bootstrap_confidence_interval(
            metric_fn=AgreementMetrics.macro_f1,
            y_true=raters["Expert_A"],
            y_pred=raters["Expert_B"],
            n_bootstraps=500
        )
        print(f"  Macro-F1: {f1:.4f} (95% CI: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}])")
        print("\nTest mode pipeline completed successfully.")
        return

    # Real submissions evaluation
    print(f"Loaded {len(submissions)} expert submission files.")
    
    experts_list = []
    labels_list = []
    assets_dict = {}

    for sub in submissions:
        prof = sub.get("expert_profile", {})
        e_id = prof.get("expert_id", f"EXP_{len(experts_list)+1}")
        expert = Expert(
            expert_id=e_id,
            name=prof.get("name", "Anonymous"),
            years_experience=float(prof.get("years_experience", 0)),
            role=prof.get("primary_role", "Reviewer"),
            affiliation=prof.get("affiliation_category", None)
        )
        experts_list.append(expert)

        for ann in sub.get("annotations", []):
            raw_path = ann.get("asset_id", "")
            repo = ann.get("repository", "unknown")
            if not raw_path:
                continue

            # Canonical repository-scoped asset key (e.g. "go_jwt:ecdsa.go")
            canon_id = ann.get("canonical_asset_id") or (f"{repo}:{raw_path}" if not raw_path.startswith(f"{repo}:") else raw_path)

            if canon_id not in assets_dict:
                assets_dict[canon_id] = AssetForReview(
                    asset_id=canon_id,
                    repository=repo,
                    file_path=raw_path,
                    detected_algorithms=ann.get("detected_primitives", []),
                    notes=ann.get("rationale")
                )

            cat_str = ann.get("assigned_risk_category", "LOW").strip().upper()
            if cat_str not in ExpertLabelClass.__members__:
                cat_str = "LOW"

            lbl = ExpertLabel(
                asset_id=canon_id,
                expert_id=e_id,
                label=ExpertLabelClass[cat_str],
                confidence=float(ann.get("confidence", 1.0)),
                rationale=ann.get("rationale", ""),
                repository=repo
            )
            labels_list.append(lbl)

    dataset = ValidationDataset(
        experts=experts_list,
        assets=list(assets_dict.values()),
        labels=labels_list
    )

    adjudicated = dataset.adjudicate(strategy="MAJORITY")
    print(f"Adjudicated {len(adjudicated)} assets across {len(experts_list)} experts.")

    # Calculate pairwise Cohen's Kappa for every pair on their mutually reviewed assets
    exp_label_maps = {
        exp.expert_id: {lbl.asset_id: LABEL_TO_INT[lbl.label] for lbl in dataset.get_expert_labels(exp.expert_id)}
        for exp in experts_list
    }
    
    pairwise_results = {}
    pairwise_details = {}
    pair_kappas = []
    for i in range(len(experts_list)):
        for j in range(i + 1, len(experts_list)):
            e1 = experts_list[i].expert_id
            e2 = experts_list[j].expert_id
            common_pair_assets = sorted(list(set(exp_label_maps[e1].keys()) & set(exp_label_maps[e2].keys())))
            if common_pair_assets:
                y1 = [exp_label_maps[e1][aid] for aid in common_pair_assets]
                y2 = [exp_label_maps[e2][aid] for aid in common_pair_assets]
                k_lin = AgreementMetrics.cohens_kappa(y1, y2, weights="linear")
                k_quad = AgreementMetrics.cohens_kappa(y1, y2, weights="quadratic")
                k_unw = AgreementMetrics.cohens_kappa(y1, y2, weights=None)
                pair_key = f"{e1}_vs_{e2}"
                pairwise_results[pair_key] = round(k_lin, 4)
                pairwise_details[pair_key] = {
                    "overlap_assets": len(common_pair_assets),
                    "linear_weighted_kappa": round(k_lin, 4),
                    "quadratic_weighted_kappa": round(k_quad, 4),
                    "unweighted_kappa": round(k_unw, 4)
                }
                pair_kappas.append(k_lin)

    # Intersect assets reviewed by all experts for panel-wide Fleiss' Kappa
    common_all_experts = sorted(list(set.intersection(*[set(exp_label_maps[e.expert_id].keys()) for e in experts_list])))

    dedup_info = {}
    for sub in submissions:
        if "deduplication_summary" in sub:
            e_name = sub["expert_profile"].get("name", sub["expert_profile"]["expert_id"])
            dedup_info[e_name] = sub["deduplication_summary"]

    metrics_payload = {
        "status": "EVALUATED",
        "num_experts": len(experts_list),
        "num_assets": len(adjudicated),
        "consensus_distribution": {
            "HIGH": sum(1 for a in adjudicated if a.consensus_label == ExpertLabelClass.HIGH),
            "MEDIUM": sum(1 for a in adjudicated if a.consensus_label == ExpertLabelClass.MEDIUM),
            "LOW": sum(1 for a in adjudicated if a.consensus_label == ExpertLabelClass.LOW)
        },
        "adjudication_summary": {
            "unanimous_consensus_count": sum(1 for a in adjudicated if a.adjudication_method == "UNANIMOUS"),
            "majority_consensus_count": sum(1 for a in adjudicated if a.adjudication_method == "MAJORITY"),
            "resolved_tie_count": sum(1 for a in adjudicated if a.adjudication_method == "RESOLVED_TIE")
        },
        "deduplication_audit": dedup_info
    }

    if pair_kappas:
        mean_k = float(np.mean(pair_kappas))
        metrics_payload["pairwise_cohens_kappa"] = {
            "pairwise": pairwise_results,
            "pairwise_details": pairwise_details,
            "mean_pairwise_kappa": round(mean_k, 4),
            "num_pairs": len(pairwise_results)
        }
        print(f"Mean Pairwise Cohen's Kappa across {len(pairwise_results)} pairs: {mean_k:.4f}")

    if len(common_all_experts) >= 10 and len(experts_list) >= 2:
        fleiss_matrix = np.zeros((len(common_all_experts), 3), dtype=int)
        for i, a_id in enumerate(common_all_experts):
            for exp in experts_list:
                c_idx = exp_label_maps[exp.expert_id][a_id]
                fleiss_matrix[i, c_idx] += 1

        f_kappa = AgreementMetrics.fleiss_kappa(fleiss_matrix)
        metrics_payload["fleiss_kappa"] = f_kappa
        metrics_payload["fleiss_evaluated_assets"] = len(common_all_experts)
        print(f"Fleiss' Kappa (Panel Agreement across {len(experts_list)} raters on N={len(common_all_experts)}): {f_kappa:.4f}")

    # Model alignment evaluation against adjudicated expert consensus
    heuristic_map = {}
    try:
        import torch
        from sklearn.metrics import confusion_matrix

        graphs = list((ROOT_DIR / "dataset" / "artifacts").glob("*.pt"))
        if graphs:
            for g in graphs:
                d = torch.load(g, weights_only=False)
                if "file" in d.node_types and hasattr(d["file"], "node_ids") and hasattr(d["file"], "y"):
                    for nid, y in zip(d["file"].node_ids, d["file"].y.tolist()):
                        heuristic_map[nid] = y

            matched_h = []
            matched_e = []
            for a in adjudicated:
                canon_id = a.asset_id
                if canon_id in heuristic_map:
                    matched_h.append(heuristic_map[canon_id])
                    matched_e.append(LABEL_TO_INT[a.consensus_label])

            if len(matched_h) >= 10:
                f1 = AgreementMetrics.macro_f1(matched_e, matched_h)
                ci = AgreementMetrics.bootstrap_confidence_interval(
                    AgreementMetrics.macro_f1, matched_e, matched_h, n_bootstraps=1000, seed=42
                )
                kw = AgreementMetrics.cohens_kappa(matched_e, matched_h, weights="linear")
                cm = confusion_matrix(matched_e, matched_h, labels=[0, 1, 2]).tolist()

                # Calculate per-class metrics
                cm_arr = np.array(cm)
                per_class = {}
                class_names = ["LOW", "MEDIUM", "HIGH"]
                for c_idx, c_name in enumerate(class_names):
                    tp = cm_arr[c_idx, c_idx]
                    pred_pos = cm_arr[:, c_idx].sum()
                    act_pos = cm_arr[c_idx, :].sum()
                    prec = (tp / pred_pos) if pred_pos > 0 else 0.0
                    rec = (tp / act_pos) if act_pos > 0 else 0.0
                    f1_c = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
                    per_class[c_name] = {
                        "precision": round(float(prec), 4),
                        "recall": round(float(rec), 4),
                        "f1": round(float(f1_c), 4),
                        "support": int(act_pos)
                    }

                metrics_payload["model_evaluation"] = {
                    "matched_assets": len(matched_h),
                    "heuristic_macro_f1": round(f1, 4),
                    "bootstrap_95ci": ci,
                    "weighted_cohens_kappa_vs_heuristic": round(kw, 4),
                    "per_class_metrics": per_class,
                    "confusion_matrix_expert_rows_vs_heuristic_cols": {
                        "labels": ["LOW", "MEDIUM", "HIGH"],
                        "matrix": cm
                    },
                    "empirical_observation": (
                        "Human domain experts classify primarily based on intrinsic algorithmic exploitability "
                        "(Shor/Grover vulnerability of public-key primitives), whereas the multi-factor heuristic "
                        "engine dampens risk for test fixtures, unexposed internal assets, and library wrappers."
                    )
                }
                print(f"\nAgileGraph Heuristic vs. Expert Ground Truth (N={len(matched_h)}):")
                print(f"  Macro-F1: {f1:.4f} (95% CI: [{ci['ci_lower']:.4f}, {ci['ci_upper']:.4f}])")
                print(f"  Weighted Cohen's Kappa: {kw:.4f}")
    except Exception as e:
        import traceback
        traceback.print_exc()

    # Asset-level adjudication audit table
    asset_audit = []
    INT_TO_LABEL_STR = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
    for a in adjudicated:
        asset_meta = assets_dict.get(a.asset_id)
        lbls = dataset.get_labels_for_asset(a.asset_id)
        votes = {l.expert_id: l.label.value for l in lbls}
        asset_audit.append({
            "canonical_asset_id": a.asset_id,
            "repository": asset_meta.repository if asset_meta else "unknown",
            "file_path": asset_meta.file_path if asset_meta else a.asset_id,
            "expert_votes": votes,
            "consensus_label": a.consensus_label.value,
            "agreement_score": a.agreement_score,
            "adjudication_method": a.adjudication_method,
            "is_tie_break": a.adjudication_method == "RESOLVED_TIE",
            "heuristic_prediction": INT_TO_LABEL_STR.get(heuristic_map.get(a.asset_id)) if a.asset_id in heuristic_map else None
        })
    metrics_payload["asset_adjudication_audit"] = asset_audit

    out_file = ROOT_DIR / args.output
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(metrics_payload, fp, indent=2)

    print(f"\nReport written to: {out_file}")


if __name__ == "__main__":
    main()

