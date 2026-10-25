"""
Tests for Benchmark Manifest, Pinned Revisions, Baseline Reproducibility,
and Provenance Integrity in Step 3.
"""
import os
import json
import pytest
import subprocess
from src.dataset.models import CorpusManifest
from src.ml.baselines import HeuristicBaseline, RuleBasedBaseline
from src.ml.experiment import RuleConfig
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCHMARK_DIR = os.path.join(BACKEND_DIR, "dataset", "benchmark")
CORPUS_DIR = os.path.join(BACKEND_DIR, "dataset", "corpus")

def test_benchmark_manifest_structure_and_pinned_revisions():
    manifest_path = os.path.join(BENCHMARK_DIR, "benchmark_manifest.json")
    assert os.path.exists(manifest_path), f"Manifest file missing: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = CorpusManifest(**data)
    assert len(manifest.projects) == 8, f"Expected 8 benchmark repositories, found {len(manifest.projects)}"

    langs = {p.language.value for p in manifest.projects}
    assert langs == {"PYTHON", "JAVA", "GO"}, f"All three languages must be represented: {langs}"

    sizes = {p.size_tier.value for p in manifest.projects}
    assert sizes == {"SMALL", "LARGE"}, f"Both size tiers must be represented: {sizes}"

    for p in manifest.projects:
        assert p.commit_sha and len(p.commit_sha) == 40, f"Invalid pinned commit SHA for {p.project_id}"
        assert p.repository_url.startswith("https://github.com/")
        repo_local = os.path.join(CORPUS_DIR, p.project_id)
        if os.path.exists(repo_local):
            curr_sha = subprocess.check_output("git rev-parse HEAD", shell=True, cwd=repo_local, text=True).strip()
            assert curr_sha == p.commit_sha, f"Local repo {p.project_id} does not match pinned commit {p.commit_sha}"


def test_benchmark_summary_data_integrity():
    summary_path = os.path.join(BENCHMARK_DIR, "benchmark_summary.json")
    assert os.path.exists(summary_path), f"Summary file missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    repo_items = {k: v for k, v in summary.items() if not k.startswith("__")}
    assert len(repo_items) == 8
    for repo_id, r in repo_items.items():
        prov = r["provenance"]
        assert prov["scanned_files"] > 0
        assert prov["errors"] == 0
        assert prov["is_mock"] is False

        # Verify all 6 node counts exist
        nc = r["node_counts"]
        for cat in ["file", "crypto_usage", "certificate", "endpoint", "library", "sensitive_data"]:
            assert cat in nc, f"Missing category {cat} in {repo_id}"

        # Verify all 7 relationship counts exist
        rc = r["relationship_counts"]
        for rel in ["CONTAINS", "IMPORTS", "CALLS", "USES_CERT", "EXPOSES", "PROTECTS", "DEPENDS_ON"]:
            assert rel in rc, f"Missing relationship {rel} in {repo_id}"

        # Verify baseline entries
        base = r["baselines"]
        assert base["heuristic_rated_count"] >= base["comparable_assets_count"]


def test_rule_based_baseline_reproducibility():
    """Verify rule-based baseline executes deterministically on a known graph fixture."""
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_md5.py", category="file"))
    ag.add_node(GraphNode(id="cu_md5", category="crypto_usage", properties={"algorithm": "md5"}))
    ag.add_edge(GraphEdge(source_id="file_md5.py", target_id="cu_md5", relationship="CONTAINS"))

    ag.add_node(GraphNode(id="file_aes.py", category="file"))
    ag.add_node(GraphNode(id="cu_aes", category="crypto_usage", properties={"algorithm": "aes"}))
    ag.add_edge(GraphEdge(source_id="file_aes.py", target_id="cu_aes", relationship="CONTAINS"))

    config = RuleConfig(version="rule-baseline-v1.0", rules=["HIGH_RISK_ALGO", "MED_RISK_ALGO"])
    baseline = RuleBasedBaseline(ag, config)
    output = baseline.evaluate()

    assert output.scores["file_md5.py"] == 0.9
    assert output.scores["file_aes.py"] == 0.3
    assert output.audit_trail["config_version"] == "rule-baseline-v1.0"
