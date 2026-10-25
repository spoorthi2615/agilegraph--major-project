"""
Corpus Summary and Factor Missingness Analysis.

Computes descriptive distributions of heuristic risk classes, factor missingness masks,
and cross-language distributions across generated benchmark corpus artifacts (corpus_v1).
"""

import os
import sys
import json
import torch
import numpy as np
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)

from src.dataset.models import CorpusManifest

ARTIFACTS_DIR = os.path.join(BACKEND_DIR, "dataset", "artifacts")


def run_analysis():
    manifest_path = os.path.join(ARTIFACTS_DIR, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}. Run build_corpus.py first.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = CorpusManifest(**json.load(f))
        
    all_labels = []
    labels_by_proj = {}
    labels_by_lang = {}
    
    missingness_counts = {
        "data_sensitivity": 0,
        "asset_criticality": 0,
        "internet_exposure": 0,
        "crypto_weakness": 0,
        "cve_risk": 0,
        "library_centrality": 0,
        "migration_difficulty": 0
    }
    factor_names = list(missingness_counts.keys())
    total_scored_assets = 0

    for p in manifest.projects:
        artifact_path = os.path.join(ARTIFACTS_DIR, f"{p.project_id}.pt")
        if not os.path.exists(artifact_path):
            continue
        pyg_data = torch.load(artifact_path, weights_only=False)
        
        if "file" not in pyg_data.node_types:
            continue
            
        features = pyg_data["file"].x
        num_assets = features.size(0)
        total_scored_assets += num_assets
        
        # Weak-supervision labels y
        if hasattr(pyg_data["file"], "y"):
            y_vals = pyg_data["file"].y.numpy().tolist()
            all_labels.extend(y_vals)
            labels_by_proj[p.project_id] = y_vals
        else:
            y_vals = []
        
        lang = p.language.value
        if lang not in labels_by_lang:
            labels_by_lang[lang] = []
        labels_by_lang[lang].extend(y_vals)
        
        # Masks are index 7 to 13
        masks = features[:, 7:14]
        for i, name in enumerate(factor_names):
            missingness_counts[name] += masks[:, i].sum().item()

    print("=== Corpus Heuristic Summary (Descriptive Analysis) ===")
    print(f"Total file assets: {total_scored_assets}")
    
    if all_labels:
        low_count = sum(1 for y in all_labels if y == 0)
        med_count = sum(1 for y in all_labels if y == 1)
        high_count = sum(1 for y in all_labels if y == 2)
        unlabeled_count = sum(1 for y in all_labels if y < 0)
        
        print("\n1. Weak-Supervision Target Label Distribution:")
        print(f"  LOW (0):      {low_count} / {len(all_labels)} ({low_count/len(all_labels)*100:.1f}%)")
        print(f"  MEDIUM (1):   {med_count} / {len(all_labels)} ({med_count/len(all_labels)*100:.1f}%)")
        print(f"  HIGH (2):     {high_count} / {len(all_labels)} ({high_count/len(all_labels)*100:.1f}%)")
        if unlabeled_count > 0:
            print(f"  UNLABELED (-1): {unlabeled_count} / {len(all_labels)} ({unlabeled_count/len(all_labels)*100:.1f}%)")
        
        print("\n2. Missing-Factor Distribution (assets missing the factor):")
        for k, v in missingness_counts.items():
            pct = (v / total_scored_assets) * 100 if total_scored_assets > 0 else 0.0
            print(f"  {k}: {int(v)} / {total_scored_assets} ({pct:.1f}%)")
            
        print("\n3. Class Breakdown by Project:")
        for proj, y_list in labels_by_proj.items():
            if y_list:
                l = sum(1 for y in y_list if y == 0)
                m = sum(1 for y in y_list if y == 1)
                h = sum(1 for y in y_list if y == 2)
                u = sum(1 for y in y_list if y < 0)
                print(f"  {proj}: Low={l}, Med={m}, High={h}, Unlabeled={u} (N={len(y_list)})")
            else:
                print(f"  {proj}: No file assets")
                
        print("\n4. Class Breakdown by Language:")
        for lang, y_list in labels_by_lang.items():
            if y_list:
                l = sum(1 for y in y_list if y == 0)
                m = sum(1 for y in y_list if y == 1)
                h = sum(1 for y in y_list if y == 2)
                u = sum(1 for y in y_list if y < 0)
                print(f"  {lang}: Low={l}, Med={m}, High={h}, Unlabeled={u} (N={len(y_list)})")
    
    print("\nDISCLAIMER: These are descriptive operational outputs based on heuristic priors; not formal security-proof guarantees.")


if __name__ == "__main__":
    run_analysis()
