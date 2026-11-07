import os
import stat as _stat
import networkx as nx
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.risk.heuristic import calculate_heuristic_score, derive_heuristic_label
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.risk.factor_extractor import FactorExtractor
from src.risk.factors import FactorValue, RiskFactors
from src.risk.experimental_heuristic import (
    calculate_experimental_heuristic_score,
    ExperimentalHeuristicConfig,
    propagate_graph_crypto_weakness_nx,
    derive_heuristic_label_v2,
)
from src.scanners.common.enums import Language
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.dependencies.scanner import scan_manifest
from src.scanners.certificates.scanner import scan_certificate_file, scan_certificate_in_code
from src.scanners.endpoints.scanner import scan_endpoints
from src.scanners.sensitive_data.scanner import scan_sensitive_data

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".tox",
    ".mypy_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

def run_pipeline(
    repository_path: str,
    project_id: str,
    missing_data_policy: str = "RENORMALIZE",
    allowed_root: str = None,
    engine_version: str = "v1"
):
    # Establish canonical root for scan
    canonical_repo = os.path.realpath(repository_path)
    if allowed_root:
        canonical_allowed = os.path.realpath(allowed_root)
        try:
            if os.path.commonpath([canonical_allowed, canonical_repo]) != canonical_allowed:
                raise ValueError("Repository path is outside allowed scan root.")
        except ValueError:
            raise ValueError("Repository path is outside allowed scan root.")
            
    if not os.path.exists(canonical_repo):
        raise ValueError("Repository path does not exist.")
        
    policy = MissingDataPolicy(missing_data_policy)
        
    findings = []
    scanned_files_count = 0
    scanner_errors = []
    
    for root, dirs, files in os.walk(canonical_repo):
        # Prune VCS, dependency bundles, virtual environments, and build/bytecode cache directories
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDED_DIRS]
        for file in files:
            if file.startswith("~$") or file.endswith((".tmp", ".temp")):
                continue

            path = os.path.join(root, file)
            canonical_file = os.path.realpath(path)
            
            # Reject non-regular files BEFORE any read — prevents FIFO hangs
            # and device reads. Use lstat on the original path so symlinks to
            # non-regular files are also caught at their source.
            try:
                lst = os.lstat(path)           # follow_symlinks=False equivalent
                cst = os.stat(canonical_file)  # stat the resolved target
            except OSError as e:
                scanner_errors.append({"file": file, "error": f"stat failed: {e}"})
                continue
            
            if not _stat.S_ISREG(cst.st_mode):
                scanner_errors.append({"file": file, "error": "Non-regular file (FIFO/device/socket) — skipped"})
                continue

            # Symlink check: lstat on original tells us if it IS a symlink
            if _stat.S_ISLNK(lst.st_mode):
                scanner_errors.append({"file": file, "error": "Symlink — skipped for security"})
                continue

            # Containment check on the canonical (fully resolved) path.
            # This catches hardlinks whose resolved path escapes the root.
            try:
                if os.path.commonpath([canonical_repo, canonical_file]) != canonical_repo:
                    scanner_errors.append({"file": file, "error": "Canonical path is outside scan root — skipped"})
                    continue
            except ValueError:
                scanner_errors.append({"file": file, "error": "Path escape detected — skipped"})
                continue
                
            rel_path = os.path.relpath(canonical_file, canonical_repo).replace("\\", "/")
            
            scanned_files_count += 1
            
            lower_file = file.lower()
            is_cert = lower_file.endswith((".crt", ".pem", ".cer", ".der", ".key"))
            is_python = file.endswith(".py")
            is_java = file.endswith(".java")
            is_go = file.endswith(".go")
            is_manifest = file in ["requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "go.mod"]
            
            # Fast-path skip: do not read non-target or binary files into memory
            if not (is_cert or is_python or is_java or is_go or is_manifest):
                continue

            # Protect against runaway memory allocation on huge files (> 10MB)
            if cst.st_size > 10 * 1024 * 1024:
                scanner_errors.append({"file": rel_path, "error": "File exceeds 10MB limit — skipped"})
                continue

            try:
                # Open the CANONICAL file — the same inode we validated.
                # This eliminates the TOCTOU race: validate and open are on
                # the same resolved path, not on a mutable original path.
                with open(canonical_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    
                if is_cert:
                    findings.extend(scan_certificate_file(project_id, rel_path, content))
                elif is_python:
                    findings.extend(scan_python_code(project_id, rel_path, content))
                    findings.extend(scan_certificate_in_code(project_id, rel_path, content, Language.PYTHON))
                    findings.extend(scan_endpoints(project_id, rel_path, content, Language.PYTHON))
                    findings.extend(scan_sensitive_data(project_id, rel_path, content, Language.PYTHON))
                elif is_java:
                    findings.extend(scan_java_code(project_id, rel_path, content))
                    findings.extend(scan_certificate_in_code(project_id, rel_path, content, Language.JAVA))
                    findings.extend(scan_endpoints(project_id, rel_path, content, Language.JAVA))
                    findings.extend(scan_sensitive_data(project_id, rel_path, content, Language.JAVA))
                elif is_go:
                    findings.extend(scan_go_code(project_id, rel_path, content))
                    findings.extend(scan_certificate_in_code(project_id, rel_path, content, Language.GO))
                    findings.extend(scan_endpoints(project_id, rel_path, content, Language.GO))
                    findings.extend(scan_sensitive_data(project_id, rel_path, content, Language.GO))
                    
                if is_manifest:
                    findings.extend(scan_manifest(project_id, rel_path, content))
            except Exception as e:
                scanner_errors.append({"file": rel_path, "error": str(e)})
                
    agile_graph = AgileGraph()
    builder = GraphBuilder(agile_graph)
    builder.build_from_normalized_records(findings)
    g = agile_graph.G
    
    extractor = FactorExtractor(agile_graph)
    scored_assets = []
    unrated_assets = []
    
    # Canonical heuristic weights from config (sum strictly to 1.0)
    weights = HeuristicWeights.from_config()

    # Pre-compute graph weakness propagation for V2 (semantic crypto imports)
    v2_config = ExperimentalHeuristicConfig(
        calibrated_low_threshold=0.18,
        calibrated_high_threshold=0.38
    )
    propagated_weakness_map = propagate_graph_crypto_weakness_nx(agile_graph, config=v2_config)
    active_engine = (engine_version or "v1").lower()

    for node, data in g.nodes(data=True):
        if data.get("category") == "file":
            props = dict(data)
            if "properties" in data and isinstance(data["properties"], dict):
                props.update(data["properties"])
            factors_v1 = extractor.extract(node, props, {}, {})
            factors_v2 = extractor.extract(node, props, {}, {})
            if node in propagated_weakness_map and factors_v2.crypto_weakness.value is None:
                factors_v2.crypto_weakness = FactorValue(
                    value=propagated_weakness_map[node],
                    source="graph_propagated_structural_weakness",
                    confidence=0.8
                )

            try:
                score_res_v1 = calculate_heuristic_score(factors_v1, weights, policy=policy)
                score_res_v2 = calculate_experimental_heuristic_score(factors_v2, weights, policy=policy, config=v2_config)

                v1_score_val = score_res_v1.score
                v2_score_val = score_res_v2.score
                v1_label = derive_heuristic_label(v1_score_val) if v1_score_val is not None else None
                v2_label = derive_heuristic_label_v2(v2_score_val, low_th=0.18, high_th=0.38) if v2_score_val is not None else None

                # Persist version-specific scores on graph node without collision
                g.nodes[node]["v1_score"] = v1_score_val
                g.nodes[node]["v1_label"] = v1_label
                g.nodes[node]["v2_score"] = v2_score_val
                g.nodes[node]["v2_label"] = v2_label

                if active_engine == "v2":
                    score_res = score_res_v2
                    active_score_val = v2_score_val
                    active_label = v2_label
                else:
                    score_res = score_res_v1
                    active_score_val = v1_score_val
                    active_label = v1_label

                score_dict = score_res.model_dump()
                score_dict["asset_id"] = node
                score_dict["engine_version"] = active_engine
                score_dict["v1_score"] = v1_score_val
                score_dict["v1_label"] = v1_label
                score_dict["v2_score"] = v2_score_val
                score_dict["v2_label"] = v2_label
                score_dict["comparison"] = {
                    "v1": {"score": v1_score_val, "label": v1_label, "formula_version": "heuristic-v1.0"},
                    "v2": {"score": v2_score_val, "label": v2_label, "formula_version": "heuristic-v2.0-experimental"}
                }

                # If file contains crypto usages but none could be rated (e.g. unrecognized algorithm),
                # it cannot be scored and must remain unrated.
                has_crypto_usages = any(g.nodes[t].get("category") == "crypto_usage" for _, t in g.out_edges(node))
                if has_crypto_usages and factors_v1.crypto_weakness.value is None and active_engine == "v1":
                    score_dict["score"] = None
                    unrated_assets.append(score_dict)
                elif active_score_val is None:
                    unrated_assets.append(score_dict)
                else:
                    if active_label:
                        score_dict["heuristic_label"] = active_label
                        g.nodes[node]["heuristic_label"] = active_label
                    g.nodes[node]["base_risk"] = active_score_val
                    g.nodes[node]["engine_version"] = active_engine
                    scored_assets.append(score_dict)
            except ValueError:
                # STRICT policy violation — record as skipped
                scanner_errors.append({"file": node, "error": "STRICT policy: missing required factors"})

    all_scores = scored_assets + unrated_assets

    return {
        "graph": g,
        "scores": all_scores,
        "provenance": {
            "scanned_files": scanned_files_count,
            "findings_count": len(findings),
            "scored_assets": len(scored_assets),
            "unrated_assets": len(unrated_assets),
            "skipped_files": len(scanner_errors),
            "errors": len(scanner_errors),
            "error_details": scanner_errors,
            "engine_version": active_engine,
            "available_engine_versions": ["v1", "v2"],
            "is_mock": False
        }
    }
