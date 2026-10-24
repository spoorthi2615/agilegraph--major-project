"""
Comprehensive Benchmark Execution and Baseline Evaluation for AgileGraph Step 3B.
Runs all 8 pinned benchmark repositories, records detailed file accounting,
node/edge distributions, factor coverage, and evaluates Heuristic vs Rule-based baselines
with bootstrap confidence intervals and paired permutation testing.
"""

import os
import sys
import json
import time
import subprocess
import numpy as np
from scipy import stats
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("src"))

from src.pipeline.runner import run_pipeline
from src.ml.baselines import HeuristicBaseline, RuleBasedBaseline
from src.ml.experiment import RuleConfig, BaselineOutput
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.dataset.models import CorpusManifest, CorpusProject, Language, SizeTier, DataOrigin, ProjectStatus, ScannerProvenance, GraphProvenance

BENCHMARK_REPOS = [
    {
        "id": "python_itsdangerous",
        "url": "https://github.com/pallets/itsdangerous",
        "sha": "672971d66a2ef9f85151e53283113f33d642dabd",
        "language": Language.PYTHON,
        "size_tier": SizeTier.SMALL,
        "license": "BSD-3-Clause",
        "rationale": "Cryptographic signing and token serialization library used widely across Flask/Pallets."
    },
    {
        "id": "python_bcrypt",
        "url": "https://github.com/pyca/bcrypt",
        "sha": "59b41aaa24c025d1cd231c37d2755b94184a3e67",
        "language": Language.PYTHON,
        "size_tier": SizeTier.SMALL,
        "license": "Apache-2.0",
        "rationale": "Password-hashing cryptographic library binding native C implementations."
    },
    {
        "id": "python_cryptography",
        "url": "https://github.com/pyca/cryptography",
        "sha": "f0ba3000a365d44db153362e847c88339c9231f4",
        "language": Language.PYTHON,
        "size_tier": SizeTier.LARGE,
        "license": "Apache-2.0 / BSD-3-Clause",
        "rationale": "De-facto standard Python cryptographic primitives and hazmat library."
    },
    {
        "id": "java_java_jwt",
        "url": "https://github.com/auth0/java-jwt",
        "sha": "29f252b2d6fea74df6576803d5fce5f6d6799cf3",
        "language": Language.JAVA,
        "size_tier": SizeTier.SMALL,
        "license": "MIT",
        "rationale": "Standard Auth0 JSON Web Token implementation in Java."
    },
    {
        "id": "java_jjwt",
        "url": "https://github.com/jwtk/jjwt",
        "sha": "fb71496164c71442d08adec4571d9616ed5e1b8d",
        "language": Language.JAVA,
        "size_tier": SizeTier.LARGE,
        "license": "Apache-2.0",
        "rationale": "Extensive enterprise Java JWT library supporting diverse signature and encryption algorithms."
    },
    {
        "id": "go_jwt",
        "url": "https://github.com/golang-jwt/jwt",
        "sha": "73c870b18e68b6e654b2b03f485aa3c9fab32cea",
        "language": Language.GO,
        "size_tier": SizeTier.SMALL,
        "license": "MIT",
        "rationale": "Primary community-maintained Golang implementation of JSON Web Tokens."
    },
    {
        "id": "go_jwt_go",
        "url": "https://github.com/dgrijalva/jwt-go",
        "sha": "9742bd7fca1c67ba2eb793750f56ee3094d1b04f",
        "language": Language.GO,
        "size_tier": SizeTier.SMALL,
        "license": "MIT",
        "rationale": "Historical Golang JWT library with diverse cryptographic test fixtures."
    },
    {
        "id": "go_crypto",
        "url": "https://github.com/golang/crypto",
        "sha": "b39ff6d641ecc5bb4b241737cb0c6b646f3e12a9",
        "language": Language.GO,
        "size_tier": SizeTier.LARGE,
        "license": "BSD-3-Clause",
        "rationale": "Official Go supplementary cryptography packages covering SSH, OpenPGP, and diverse ciphers."
    }
]

CORPUS_ROOT = "dataset/corpus"
OUTPUT_DIR = "dataset/benchmark_step3"


def compute_baseline_statistics(h_scores: List[float], r_scores: List[float]) -> Dict[str, Any]:
    n = len(h_scores)
    if n < 2:
        return {
            "status": "UNDEFINED",
            "comparable_assets_count": n,
            "spearman_rho": None,
            "spearman_pvalue": None,
            "kendall_tau": None,
            "kendall_pvalue": None,
            "bootstrap_ci_spearman_95": None,
            "paired_permutation_pvalue": None,
            "reason": "Sample size N < 2 is insufficient for rank correlation."
        }

    h_arr = np.array(h_scores, dtype=float)
    r_arr = np.array(r_scores, dtype=float)

    # Paired permutation test: test null hypothesis H0: E[s_heuristic - s_rule] = 0 (paired exchangeability)
    rng = np.random.default_rng(42)
    obs_diff = np.mean(h_arr - r_arr)
    swaps = rng.choice([-1.0, 1.0], size=(10000, n))
    diff_vector = h_arr - r_arr
    perm_diffs = np.mean(swaps * diff_vector, axis=1)
    extreme_count = int(np.sum(np.abs(perm_diffs) >= np.abs(obs_diff)))
    # Finite-sample correction (Davison & Hinkley 1997, Phipson & Smyth 2010): (k + 1) / (B + 1)
    perm_p = float((extreme_count + 1) / (10000 + 1))
    perm_details = {
        "null_hypothesis": "E[s_heuristic - s_rule] = 0 under paired sign exchangeability",
        "test_statistic": "|mean(s_heuristic - s_rule)|",
        "observed_statistic": round(float(np.abs(obs_diff)), 4),
        "num_permutations": 10000,
        "extreme_outcomes_count": extreme_count,
        "finite_sample_corrected_pvalue": round(perm_p, 6)
    }

    # Check if either array has zero variance (constant score vector)
    std_h = float(np.std(h_arr))
    std_r = float(np.std(r_arr))
    if std_h == 0.0 or std_r == 0.0:
        which_constant = []
        if std_h == 0.0:
            which_constant.append("heuristic_scores")
        if std_r == 0.0:
            which_constant.append("rule_scores")
        return {
            "status": "UNDEFINED",
            "comparable_assets_count": n,
            "spearman_rho": None,
            "spearman_pvalue": None,
            "kendall_tau": None,
            "kendall_pvalue": None,
            "bootstrap_ci_spearman_95": None,
            "paired_permutation_pvalue": round(perm_p, 6),
            "permutation_test_details": perm_details,
            "mean_score_difference": round(float(obs_diff), 4),
            "reason": f"Zero variance (constant score vector) in: {', '.join(which_constant)}. Rank correlation is mathematically undefined."
        }

    spearman_res = stats.spearmanr(h_arr, r_arr)
    kendall_res = stats.kendalltau(h_arr, r_arr)

    # Bootstrap 95% CI (1000 resamples)
    boot_rhos = []
    for _ in range(1000):
        idx = rng.choice(n, size=n, replace=True)
        if np.std(h_arr[idx]) > 0.0 and np.std(r_arr[idx]) > 0.0:
            val = stats.spearmanr(h_arr[idx], r_arr[idx]).statistic
            if not np.isnan(val):
                boot_rhos.append(float(val))

    if boot_rhos:
        ci_lower = round(float(np.percentile(boot_rhos, 2.5)), 4)
        ci_upper = round(float(np.percentile(boot_rhos, 97.5)), 4)
    else:
        ci_lower, ci_upper = None, None

    return {
        "status": "DEFINED",
        "comparable_assets_count": n,
        "spearman_rho": round(float(spearman_res.statistic), 4),
        "spearman_pvalue": round(float(spearman_res.pvalue), 6),
        "kendall_tau": round(float(kendall_res.statistic), 4),
        "kendall_pvalue": round(float(kendall_res.pvalue), 6),
        "bootstrap_ci_spearman_95": [ci_lower, ci_upper],
        "paired_permutation_pvalue": round(perm_p, 6),
        "permutation_test_details": perm_details,
        "mean_score_difference": round(float(obs_diff), 4)
    }


def run_benchmark():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scan_date = datetime.now(timezone.utc).isoformat()
    manifest_projects = []
    benchmark_results = {}

    rule_config = RuleConfig(version="rule-baseline-v1.0", rules=["HIGH_RISK_ALGO", "MED_RISK_ALGO", "PQC_ALGO", "UNKNOWN_CRYPTO", "INDIRECT_LIBRARY_RISK"])

    corpus_heuristic_all = []
    corpus_rule_all = []

    for r in BENCHMARK_REPOS:
        repo_id = r["id"]
        repo_dir = os.path.join(CORPUS_ROOT, repo_id)
        if not os.path.exists(repo_dir):
            print(f"Skipping {repo_id}: directory {repo_dir} does not exist")
            continue

        # Pin commit verification
        curr_sha = subprocess.check_output("git rev-parse HEAD", shell=True, cwd=repo_dir, text=True).strip()
        assert curr_sha == r["sha"], f"SHA mismatch for {repo_id}: expected {r['sha']}, found {curr_sha}"

        # File accounting at pinned commit
        ls_files = subprocess.check_output("git ls-files", shell=True, cwd=repo_dir, text=True).splitlines()
        committed_file_count = len(ls_files)

        cert_exts = ('.crt', '.pem', '.cer', '.der', '.key', '.p12', '.pfx')
        manifest_names = ('requirements.txt', 'pom.xml', 'go.mod')
        eligible_files = []
        for f in ls_files:
            lf = f.lower()
            if lf.endswith(cert_exts) or os.path.basename(f) in manifest_names:
                eligible_files.append(f)
            elif r["language"] == Language.PYTHON and f.endswith(".py"):
                eligible_files.append(f)
            elif r["language"] == Language.JAVA and f.endswith(".java"):
                eligible_files.append(f)
            elif r["language"] == Language.GO and f.endswith(".go"):
                eligible_files.append(f)

        print(f"--> Scanning benchmark repository: {repo_id} (SHA: {curr_sha[:8]})...")
        start_time = time.time()
        pipeline_res = run_pipeline(repo_dir, repo_id, allowed_root=repo_dir)
        elapsed = time.time() - start_time

        g = pipeline_res["graph"]
        scores = pipeline_res["scores"]
        provenance = pipeline_res["provenance"]

        # 1. Node counts by category
        node_counts = {
            "file": 0, "crypto_usage": 0, "certificate": 0,
            "endpoint": 0, "library": 0, "sensitive_data": 0
        }
        for _, data in g.nodes(data=True):
            cat = data.get("category", "unknown")
            if cat in node_counts:
                node_counts[cat] += 1
            else:
                node_counts[cat] = 1

        # 2. Edge counts by relationship
        rel_counts = {
            "CONTAINS": 0, "IMPORTS": 0, "CALLS": 0, "USES_CERT": 0,
            "EXPOSES": 0, "PROTECTS": 0, "DEPENDS_ON": 0
        }
        for _, _, data in g.edges(data=True):
            rel = data.get("relationship", "unknown")
            if rel in rel_counts:
                rel_counts[rel] += 1
            else:
                rel_counts[rel] = 1

        # 3. Rated vs Unrated assets
        rated_assets = [s for s in scores if s.get("score") is not None]
        unrated_assets = [s for s in scores if s.get("score") is None]

        # 4. Factor presence statistics
        factor_stats = {
            "crypto_weakness": 0,
            "data_sensitivity": 0,
            "asset_criticality": 0,
            "internet_exposure": 0,
            "cve_risk": 0,
            "library_centrality": 0,
            "migration_difficulty": 0
        }
        for s in scores:
            for fname in factor_stats.keys():
                fval = s.get("factors", {}).get(fname, {}).get("value")
                if fval is not None:
                    factor_stats[fname] += 1

        # 5. Semantic breakdown for certificates and endpoints
        cert_breakdown = {
            "parsed_x509_identities": 0,
            "raw_cert_files": 0,
            "code_loading_patterns": 0
        }
        for _, d in g.nodes(data=True):
            if d.get("category") == "certificate":
                op = d.get("operation")
                if op == "certificate_identity":
                    cert_breakdown["parsed_x509_identities"] += 1
                elif op == "certificate_file":
                    cert_breakdown["raw_cert_files"] += 1
                elif op == "certificate_loading":
                    cert_breakdown["code_loading_patterns"] += 1

        endpoint_breakdown = {
            "total_endpoints": 0,
            "internet_facing": 0,
            "internal_or_restricted": 0,
            "unknown_exposure": 0
        }
        for _, d in g.nodes(data=True):
            if d.get("category") == "endpoint":
                endpoint_breakdown["total_endpoints"] += 1
                exp = d.get("network_exposure", "UNKNOWN").upper()
                if exp == "INTERNET_FACING":
                    endpoint_breakdown["internet_facing"] += 1
                elif exp in ("INTERNAL", "RESTRICTED"):
                    endpoint_breakdown["internal_or_restricted"] += 1
                else:
                    endpoint_breakdown["unknown_exposure"] += 1

        # 6. Baseline Evaluation: Rule-based baseline
        ag = AgileGraph()
        ag.G = g
        rule_baseline = RuleBasedBaseline(ag, rule_config)
        rule_output = rule_baseline.evaluate()

        # AgileGraph Heuristic scores
        heuristic_scores = {s["asset_id"]: s["score"] for s in rated_assets}

        # Comparable asset overlap
        comparable_asset_ids = sorted(list(set(heuristic_scores.keys()) & set(rule_output.scores.keys())))
        repo_h_vec = [heuristic_scores[aid] for aid in comparable_asset_ids]
        repo_r_vec = [rule_output.scores[aid] for aid in comparable_asset_ids]

        corpus_heuristic_all.extend(repo_h_vec)
        corpus_rule_all.extend(repo_r_vec)

        repo_stats = compute_baseline_statistics(repo_h_vec, repo_r_vec)

        # File accounting reconciliation
        file_accounting = {
            "committed_files_git": committed_file_count,
            "eligible_files_by_rules": len(eligible_files),
            "excluded_by_extension_rules": committed_file_count - len(eligible_files),
            "scanned_files_walk": provenance["scanned_files"],
            "files_producing_graph_nodes": node_counts["file"],
            "eligible_files_without_findings": len(eligible_files) - node_counts["file"],
            "scan_errors": provenance["errors"]
        }

        benchmark_results[repo_id] = {
            "metadata": {
                "repository_url": r["url"],
                "commit_sha": r["sha"],
                "language": r["language"].value,
                "size_tier": r["size_tier"].value,
                "license": r["license"],
                "selection_rationale": r["rationale"],
                "scan_date": scan_date,
                "scan_duration_seconds": round(elapsed, 2)
            },
            "file_accounting": file_accounting,
            "provenance": provenance,
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
            "semantic_details": {
                "certificates": cert_breakdown,
                "endpoints": endpoint_breakdown
            },
            "asset_counts": {
                "total_scored_or_unrated": len(scores),
                "rated_assets": len(rated_assets),
                "unrated_assets": len(unrated_assets)
            },
            "factor_population_counts": factor_stats,
            "baselines": {
                "heuristic_rated_count": len(heuristic_scores),
                "rule_based_rated_count": len(rule_output.scores),
                "comparable_assets_count": len(comparable_asset_ids),
                "ndcg_k_status": "NOT_AVAILABLE (requires external ground-truth relevance labels; heuristic scores cannot serve as ground truth)",
                "correlation_statistics": repo_stats
            }
        }

        manifest_projects.append(CorpusProject(
            project_id=repo_id,
            repository_url=r["url"],
            commit_sha=r["sha"],
            language=r["language"],
            size_tier=r["size_tier"],
            origin=DataOrigin.PUBLIC_OPEN_SOURCE,
            status=ProjectStatus.READY_FOR_MODELING,
            checkout_timestamp=datetime.now(timezone.utc),
            scanner_provenance=ScannerProvenance(scanner_version="2.0", dependency_scan_version="2.0"),
            graph_provenance=GraphProvenance(graph_version="2.0", risk_calculation_version="heuristic-v0.1"),
            metadata={
                "license": r["license"],
                "rated_assets": str(len(rated_assets)),
                "unrated_assets": str(len(unrated_assets))
            }
        ))

    # Calculate corpus-wide aggregate statistics across all comparable assets
    corpus_stats = compute_baseline_statistics(corpus_heuristic_all, corpus_rule_all)

    # Repository-clustered statistics (strictly across repos with defined correlation and N >= 3)
    valid_repo_stats = []
    undefined_repos = []
    for r in BENCHMARK_REPOS:
        rid = r["id"]
        if rid in benchmark_results:
            cstats = benchmark_results[rid]["baselines"]["correlation_statistics"]
            if cstats.get("status") == "DEFINED" and cstats.get("spearman_rho") is not None and cstats.get("comparable_assets_count", 0) >= 3:
                valid_repo_stats.append((rid, cstats["comparable_assets_count"], cstats["spearman_rho"]))
            else:
                undefined_repos.append({
                    "repository": rid,
                    "comparable_assets": cstats.get("comparable_assets_count", 0),
                    "status": cstats.get("status", "UNDEFINED"),
                    "reason": cstats.get("reason", "N < 3 or undefined correlation")
                })

    unweighted_mean_rho = float(np.mean([s[2] for s in valid_repo_stats])) if valid_repo_stats else None
    total_valid_assets = sum(s[1] for s in valid_repo_stats)
    weighted_mean_rho = float(sum(s[1] * s[2] for s in valid_repo_stats) / total_valid_assets) if total_valid_assets > 0 else None

    # Clustered bootstrap across defined repository clusters (1000 resamples of repos)
    rng_clust = np.random.default_rng(42)
    clust_boot_rhos = []
    if len(valid_repo_stats) >= 3:
        for _ in range(1000):
            sample_repos = rng_clust.choice(len(valid_repo_stats), size=len(valid_repo_stats), replace=True)
            boot_rhos_repo = [valid_repo_stats[i][2] for i in sample_repos]
            clust_boot_rhos.append(float(np.mean(boot_rhos_repo)))

    clustered_ci = [
        round(float(np.percentile(clust_boot_rhos, 2.5)), 4),
        round(float(np.percentile(clust_boot_rhos, 97.5)), 4)
    ] if clust_boot_rhos else None

    benchmark_results["__corpus_aggregate__"] = {
        "total_repositories": len(BENCHMARK_REPOS),
        "total_comparable_assets": len(corpus_heuristic_all),
        "ndcg_k_status": "NOT_AVAILABLE (requires external ground-truth relevance labels; heuristic scores cannot serve as ground truth)",
        "pooled_statistics": corpus_stats,
        "repository_clustered_statistics": {
            "defined_repositories_count": len(valid_repo_stats),
            "undefined_repositories_count": len(undefined_repos),
            "unweighted_mean_spearman_rho": round(unweighted_mean_rho, 4) if unweighted_mean_rho is not None else None,
            "weighted_mean_spearman_rho": round(weighted_mean_rho, 4) if weighted_mean_rho is not None else None,
            "clustered_bootstrap_ci_spearman_95": clustered_ci,
            "limitations_note": "Inference across K=6 usable repository clusters is constrained by small sample size; cluster bootstrap interval reflects high inter-repository variance.",
            "defined_repository_contributions": [
                {"repository": s[0], "comparable_assets": s[1], "spearman_rho": s[2]} for s in valid_repo_stats
            ],
            "excluded_undefined_repositories": undefined_repos
        }
    }

    # Save benchmark manifest
    manifest = CorpusManifest(
        manifest_id="step3_benchmark_corpus_v2",
        dataset_generation_version="2.0",
        projects=manifest_projects
    )
    manifest_path = os.path.join(OUTPUT_DIR, "benchmark_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    # Save detailed benchmark results
    results_path = os.path.join(OUTPUT_DIR, "benchmark_summary.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)

    print("\nBenchmark generation finished. Output saved to:")
    print(f"  {manifest_path}")
    print(f"  {results_path}")


if __name__ == "__main__":
    run_benchmark()
