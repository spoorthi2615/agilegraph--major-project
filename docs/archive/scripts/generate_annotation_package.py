"""
AgileGraph Step 4 — Independent Expert Annotation Package Generator.
Extracts a stratified sample of 150-200 cryptographic assets across all 8 benchmark repositories
and all 3 languages (Python, Java, Go) without revealing heuristic risk scores to annotators.
"""

import os
import sys
import json
import random
import subprocess
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.pipeline.runner import run_pipeline


def generate_expert_annotation_package(
    corpus_dir: str = "dataset/corpus",
    out_path: str = "dataset/annotation/sample_annotation_package.json",
    seed: int = 42,
    target_sample_size: int = 160,
    version: str = "2.0.0"
) -> Dict[str, Any]:
    """
    Generates a reproducible, blinded expert annotation package.
    Blinding rule: Heuristic risk scores and model predictions are strictly omitted.
    """
    if not os.path.exists(corpus_dir):
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    # Pinned repository commit SHAs
    manifest_path = "dataset/benchmark_step3/benchmark_manifest.json"
    repo_commits = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            for p in manifest_data.get("projects", []):
                repo_commits[p["project_id"]] = p["commit_sha"]

    rng = random.Random(seed)

    repositories = [
        "python_itsdangerous", "python_bcrypt", "python_cryptography",
        "java_java_jwt", "java_jjwt", "go_jwt", "go_jwt_go", "go_crypto"
    ]

    # Quota allocation across repository tiers to reach ~160 assets
    # Large repos receive higher quota, small repos receive smaller quota
    quotas = {
        "python_itsdangerous": 7,    # 100% of available assets (7)
        "python_bcrypt": 2,           # 100% of available assets (2)
        "python_cryptography": 50,    # Core primitives, hazmat, ciphers
        "java_java_jwt": 20,          # Tokens, signatures, verification
        "java_jjwt": 35,              # Algorithms, providers, key loaders
        "go_jwt": 15,                 # Signing methods, RSA/HMAC/ECDSA
        "go_jwt_go": 12,              # Verification routines
        "go_crypto": 25               # SSH, OpenPGP, curve primitives
    }

    selected_assets: List[Dict[str, Any]] = []
    repo_stats: Dict[str, Any] = {}

    for repo_id in repositories:
        repo_path = os.path.join(corpus_dir, repo_id)
        if not os.path.exists(repo_path):
            print(f"Skipping missing repo {repo_id}")
            continue

        print(f"Processing {repo_id} for annotation sampling...")
        res = run_pipeline(repo_path, repo_id, allowed_root=repo_path)
        g = res["graph"]
        scores = res["scores"]
        commit_sha = repo_commits.get(repo_id, "unknown")

        # Get all file assets
        file_assets = [s["asset_id"] for s in scores]
        file_assets.sort()  # Canonical alphabetical sort before sampling

        # Stratified buckets: assets with explicit crypto_usage vs certificate vs library
        crypto_assets = []
        cert_assets = []
        other_assets = []

        for aid in file_assets:
            # Check connected nodes in graph
            if not g.has_node(aid):
                other_assets.append(aid)
                continue

            neighbors = set(g.successors(aid)) | set(g.predecessors(aid))
            categories = {g.nodes[n].get("category") for n in neighbors if g.has_node(n)}

            if "crypto_usage" in categories:
                crypto_assets.append(aid)
            elif "certificate" in categories:
                cert_assets.append(aid)
            else:
                other_assets.append(aid)

        # Shuffle each bucket deterministically
        rng.shuffle(crypto_assets)
        rng.shuffle(cert_assets)
        rng.shuffle(other_assets)

        target_quota = quotas.get(repo_id, 20)
        chosen_for_repo: List[str] = []

        # Prioritize crypto usages, then certificates, then others
        for candidate in crypto_assets + cert_assets + other_assets:
            if len(chosen_for_repo) < target_quota:
                chosen_for_repo.append(candidate)

        repo_stats[repo_id] = {
            "total_available": len(file_assets),
            "sampled": len(chosen_for_repo),
            "commit_sha": commit_sha
        }

        # Format asset dossiers for review
        for aid in chosen_for_repo:
            rel_path = aid.split(":", 1)[1] if ":" in aid else aid
            lang = "PYTHON" if "python" in repo_id else "JAVA" if "java" in repo_id else "GO"

            # Gather observable evidence from graph neighbors
            evidence_items = []
            if g.has_node(aid):
                neighbors = sorted(list(set(g.successors(aid)) | set(g.predecessors(aid))))
                for n in neighbors:
                    nd = g.nodes[n]
                    cat = nd.get("category")
                    if cat == "crypto_usage":
                        evidence_items.append({
                            "type": "CRYPTO_USAGE",
                            "api": nd.get("api"),
                            "algorithm": nd.get("algorithm"),
                            "operation": nd.get("operation"),
                            "key_size": nd.get("key_size"),
                            "snippet": nd.get("evidence"),
                            "line_number": nd.get("line_number")
                        })
                    elif cat == "certificate":
                        evidence_items.append({
                            "type": "CERTIFICATE",
                            "subject": nd.get("subject"),
                            "issuer": nd.get("issuer"),
                            "signature_algorithm": nd.get("sig_algo"),
                            "operation": nd.get("operation")
                        })
                    elif cat == "library":
                        evidence_items.append({
                            "type": "DEPENDENCY_LIBRARY",
                            "library": nd.get("library"),
                            "version": nd.get("version")
                        })
                    elif cat == "endpoint":
                        evidence_items.append({
                            "type": "ENDPOINT",
                            "route": nd.get("route"),
                            "network_exposure": nd.get("network_exposure")
                        })
                    elif cat == "sensitive_data":
                        evidence_items.append({
                            "type": "SENSITIVE_DATA",
                            "data_type": nd.get("data_type")
                        })

            # CRITICAL RESEARCH-INTEGRITY RULE:
            # We strictly DO NOT include heuristic_score in the dossier.
            asset_dossier = {
                "asset_id": aid,
                "project_id": repo_id,
                "commit_sha": commit_sha,
                "language": lang,
                "relative_path": rel_path,
                "evidence_count": len(evidence_items),
                "observable_evidence": evidence_items
            }
            selected_assets.append(asset_dossier)

    # Sort final sample deterministically by asset_id
    selected_assets.sort(key=lambda x: x["asset_id"])

    package = {
        "metadata": {
            "package_id": "agilegraph_expert_annotation_sample_v2",
            "protocol_version": version,
            "rubric_version": "2.0.0",
            "selection_seed": seed,
            "total_sampled_assets": len(selected_assets),
            "blinding_policy": "STRICT_BLINDING (no heuristic scores or model predictions revealed)",
            "languages_represented": ["PYTHON", "JAVA", "GO"],
            "target_annotators_count": 4,
            "pseudonymous_expert_ids": ["expert_01", "expert_02", "expert_03", "expert_04"],
            "sampling_distribution_by_repo": repo_stats
        },
        "instructions": (
            "Independently assess each cryptographic asset using the 7-factor rubric defined in "
            "docs/EXPERT_ANNOTATION_RUBRIC.md. Submit your judgments in the standardized JSON schema."
        ),
        "assets": selected_assets
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)

    # Also create an empty annotator submission template
    template_path = os.path.join(os.path.dirname(out_path), "expert_submission_template.json")
    submission_template = {
        "metadata": {
            "expert_id": "expert_01",
            "dataset_version": "v1",
            "annotation_protocol_version": version,
            "rubric_version": "2.0.0",
            "total_labels": len(selected_assets)
        },
        "labels": [
            {
                "asset_id": a["asset_id"],
                "project_id": a["project_id"],
                "commit_sha": a["commit_sha"],
                "expert_id": "expert_01",
                "migration_priority": "UNKNOWN",  # HIGH, MEDIUM, LOW, UNKNOWN
                "crypto_concern": "UNKNOWN_OR_UNCLASSIFIED",
                "sensitive_data_impact": "UNKNOWN_OR_INSUFFICIENT_EVIDENCE",
                "exposure": "UNKNOWN",
                "post_quantum_urgency": "INVESTIGATE_FURTHER",
                "evidence_confidence": "MEDIUM",
                "rationale": "Enter concise rationale citing code evidence or dependencies."
            }
            for a in selected_assets
        ]
    }
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(submission_template, f, indent=2)

    print(f"\nSuccessfully generated annotation package at: {out_path}")
    print(f"Successfully generated annotator template at: {template_path}")
    print(f"Total sampled assets: {len(selected_assets)}")
    return package


if __name__ == "__main__":
    generate_expert_annotation_package()
