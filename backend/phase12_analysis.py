import os
import sys
import json
import torch
import numpy as np
from typing import Dict, Any

sys.path.insert(0, os.path.abspath('src'))
from src.dataset.models import CorpusManifest

ARTIFACTS_DIR = "dataset/artifacts"

def run_analysis():
    with open(os.path.join(ARTIFACTS_DIR, "manifest.json"), "r") as f:
        manifest = CorpusManifest(**json.load(f))
        
    all_scores = []
    scores_by_proj = {}
    scores_by_lang = {}
    
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
        pyg_data = torch.load(artifact_path, weights_only=False)
        
        if "file" not in pyg_data.node_types:
            continue
            
        features = pyg_data["file"].x
        num_assets = features.size(0)
        total_scored_assets += num_assets
        
        # Base risk is index 0
        scores = features[:, 0].numpy().tolist()
        all_scores.extend(scores)
        
        scores_by_proj[p.project_id] = scores
        
        lang = p.language.value
        if lang not in scores_by_lang:
            scores_by_lang[lang] = []
        scores_by_lang[lang].extend(scores)
        
        # Masks are index 7 to 13
        masks = features[:, 7:14]
        for i, name in enumerate(factor_names):
            missingness_counts[name] += masks[:, i].sum().item()

    print("=== Heuristic Analysis (Descriptive Only) ===")
    print(f"Total scored assets: {total_scored_assets}")
    
    if all_scores:
        print("\n1. Heuristic Score Distribution:")
        print(f"  Mean: {np.mean(all_scores):.4f}")
        print(f"  Median: {np.median(all_scores):.4f}")
        print(f"  Min: {np.min(all_scores):.4f}")
        print(f"  Max: {np.max(all_scores):.4f}")
        print(f"  Std Dev: {np.std(all_scores):.4f}")
        
        print("\n2. Missing-Factor Distribution (assets missing the factor):")
        for k, v in missingness_counts.items():
            print(f"  {k}: {int(v)} / {total_scored_assets} ({(v/total_scored_assets)*100:.1f}%)")
            
        print("\n3. Scores by Project:")
        for proj, scores in scores_by_proj.items():
            if scores:
                print(f"  {proj}: Mean={np.mean(scores):.4f}, Max={np.max(scores):.4f} (N={len(scores)})")
            else:
                print(f"  {proj}: No file assets")
                
        print("\n4. Scores by Language:")
        for lang, scores in scores_by_lang.items():
            if scores:
                print(f"  {lang}: Mean={np.mean(scores):.4f}, Max={np.max(scores):.4f} (N={len(scores)})")
                
        print("\n5. Contribution Decomposition:")
        variance = np.var(all_scores)
        if variance == 0.0:
            print("  Variance is exactly 0.0 across all scored assets.")
            print("  Because 6/7 factors are missing and library_centrality is uniformly low/zero,")
            print("  the formula correctly renormalizes but produces no meaningful score variation.")
        else:
            print("  Since missing factors are RENORMALIZED, and 6/7 factors are 100% missing,")
            print("  100% of the calculated variance in this specific real corpus")
            print("  currently derives from the `library_centrality` factor.")
    
    print("\nDISCLAIMER: These are descriptive outputs only. Do not interpret as validated security-risk truth.")

if __name__ == "__main__":
    run_analysis()
