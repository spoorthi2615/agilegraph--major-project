import os
import json
import random
from src.pipeline.runner import run_pipeline
import networkx as nx

def generate_package():
    corpus_dir = "dataset/corpus"
    if not os.path.exists(corpus_dir):
        print("Corpus directory not found.")
        return

    # Seed for determinism
    random.seed(42)

    repositories = [d for d in os.listdir(corpus_dir) if os.path.isdir(os.path.join(corpus_dir, d))]
    
    all_assets = []
    asset_id_counter = 1
    
    for repo in sorted(repositories):
        repo_path = os.path.join(corpus_dir, repo)
        print(f"Scanning {repo}...")
        try:
            result = run_pipeline(repo_path, repo, "RENORMALIZE")
        except Exception as e:
            print(f"Error scanning {repo}: {e}")
            continue
            
        g = result["graph"]
        scores = result["scores"]
        
        # Collect File assets (sort for determinism before shuffling)
        file_nodes = sorted([n for n, d in g.nodes(data=True) if d.get('category') == 'file'])
        
        # Shuffle deterministically
        random.shuffle(file_nodes)
        
        # Pick up to 35 files per repository to reach 150-200 assets
        selected_nodes = file_nodes[:35]
        
        for file_node in selected_nodes:
            # Find associated factors from scores
            asset_score_info = next((s for s in scores if s["asset_id"] == file_node), None)
            
            # Find evidence (CryptoUsages)
            neighbors = sorted(list(g.successors(file_node)) + list(g.predecessors(file_node)))
            evidence = []
            for n in set(neighbors):
                node_data = g.nodes[n]
                if node_data.get('category') == 'crypto_usage':
                    evidence.append({
                        "api": node_data.get("api"),
                        "algorithm": node_data.get("algorithm"),
                        "operation": node_data.get("operation"),
                        "evidence_snippet": node_data.get("evidence"),
                        "extra": node_data.get("extra", {})
                    })
                elif node_data.get('category') == 'library':
                    evidence.append({
                        "library": node_data.get("library")
                    })
            
            # Sort evidence for deterministic output
            evidence = sorted(evidence, key=lambda x: str(x))
            
            # Record asset
            asset = {
                "id": f"asset_{asset_id_counter:03d}",
                "language": "python" if "python" in repo else "java" if "java" in repo else "go",
                "factors": asset_score_info["factors"] if asset_score_info else {},
                "factor_metadata_missing": asset_score_info["missing_factors"] if asset_score_info else [],
                "scanner_evidence": evidence
            }
            all_assets.append(asset)
            asset_id_counter += 1
            
    # Final package
    package = {
        "metadata": {
            "implementation_sha": "632e54a2e46dba9f440e2be6468a460495c87553",
            "protocol_version": "1.1.1",
            "total_assets": len(all_assets)
        },
        "instructions": "Determine the migration priority (HIGH, MEDIUM, LOW, UNKNOWN) based strictly on the provided evidence.",
        "assets": all_assets
    }
    
    os.makedirs("dataset/artifacts", exist_ok=True)
    out_path = "dataset/artifacts/expert_annotation_package_v1.2.0.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)
        
    print(f"Successfully generated annotation package at {out_path}")
    print(f"Total assets selected: {len(all_assets)}")
    
    # Analyze distribution
    langs = {}
    for a in all_assets:
        l = a["language"]
        langs[l] = langs.get(l, 0) + 1
    print(f"Language distribution: {langs}")
    
    # Check for missing evidence
    missing_evidence = sum(1 for a in all_assets if not a["scanner_evidence"])
    print(f"Assets with no direct scanner evidence: {missing_evidence}")

if __name__ == "__main__":
    generate_package()
