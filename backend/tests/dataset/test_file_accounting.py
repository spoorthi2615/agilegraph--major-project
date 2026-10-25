import os
import subprocess
import pytest
from src.dataset.models import Language
from src.pipeline.runner import run_pipeline


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CORPUS_ROOT = os.path.join(BACKEND_DIR, "dataset", "corpus")
BENCHMARK_DIR = os.path.join(BACKEND_DIR, "dataset", "benchmark")
BENCHMARK_REPOS = [
    ("python_itsdangerous", 50),
    ("python_bcrypt", 23),
    ("python_cryptography", 3072),
    ("java_java_jwt", 134),
    ("java_jjwt", 733),
    ("go_jwt", 77),
    ("go_jwt_go", 51),
    ("go_crypto", 418),
]


def test_file_accounting_zero_untracked_discrepancy():
    """
    Asserts that every pinned repository has 0 discrepancy between
    git tracked files and working tree source files (excluding .git).
    """
    for repo_id, expected_git_count in BENCHMARK_REPOS:
        repo_dir = os.path.join(CORPUS_ROOT, repo_id)
        assert os.path.exists(repo_dir), f"Missing repo directory: {repo_dir}"

        tracked = subprocess.check_output("git ls-files", shell=True, cwd=repo_dir, text=True).splitlines()
        assert len(tracked) == expected_git_count, f"Committed file count mismatch for {repo_id}: expected {expected_git_count}, got {len(tracked)}"

        working = []
        for root, dirs, files in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".pytest_cache", ".tox")]
            for f in files:
                working.append(os.path.join(root, f))

        assert len(working) == expected_git_count, f"Working tree discrepancy for {repo_id}: tracked {len(tracked)}, working {len(working)}"


def test_cache_directory_pruning_in_runner(tmp_path):
    """
    Tests that runner.py strictly prunes __pycache__, .pytest_cache, and .git directories
    from file traversal count.
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hello')", encoding="utf-8")

    # Add cache directories that should be pruned
    pycache = repo / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-313.pyc").write_bytes(b"\x00\x00")

    gitdir = repo / ".git"
    gitdir.mkdir()
    (gitdir / "config").write_text("[core]\n", encoding="utf-8")

    res = run_pipeline(str(repo), "test_repo", allowed_root=str(repo))
    # Scanned files must ONLY count main.py, NOT pyc or git config
    assert res["provenance"]["scanned_files"] == 1


def test_canonical_benchmark_accounting_and_criticality_reconciliation():
    """
    Asserts cross-artifact consistency between benchmark_manifest.json,
    benchmark_summary.json, git tracked file counts, and criticality factor counts.
    """
    import json
    summary_path = os.path.join(BENCHMARK_DIR, "benchmark_summary.json")
    assert os.path.exists(summary_path)

    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)

    manifest_path = os.path.join(BENCHMARK_DIR, "benchmark_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Manifest and summary projects must match
    manifest_ids = {p["project_id"] for p in manifest["projects"]}
    summary_ids = {k for k in summary.keys() if k != "__corpus_aggregate__"}
    assert manifest_ids == summary_ids == {r[0] for r in BENCHMARK_REPOS}

    # Verify canonical per-repo counts
    total_git = 0
    total_scanned = 0
    total_eligible = 0
    total_file_nodes = 0
    total_scored = 0
    total_crit_pop = 0

    for repo_id, exp_git in BENCHMARK_REPOS:
        r_data = summary[repo_id]
        fa = r_data["file_accounting"]
        nc = r_data["node_counts"]
        ac = r_data["asset_counts"]
        fp = r_data["factor_population_counts"]

        assert fa["committed_files_git"] == exp_git
        assert fa["scanned_files_walk"] == exp_git
        assert nc["file"] == ac["total_scored_or_unrated"]

        total_git += fa["committed_files_git"]
        total_scanned += fa["scanned_files_walk"]
        total_eligible += fa["eligible_files_by_rules"]
        total_file_nodes += nc["file"]
        total_scored += ac["total_scored_or_unrated"]
        total_crit_pop += fp["asset_criticality"]

    assert total_git == 4558
    assert total_scanned == 4558
    assert total_eligible == 2524
    assert total_file_nodes == 1458
    assert total_scored == 1458
    assert total_crit_pop == 549
    assert (total_scored - total_crit_pop) == 909  # Uncertain / None criticality count
