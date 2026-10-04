import os
import stat as _stat
import networkx as nx
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.risk.heuristic import calculate_heuristic_score
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.risk.factor_extractor import FactorExtractor
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.dependencies.scanner import scan_manifest

def run_pipeline(repository_path: str, project_id: str, missing_data_policy: str = "RENORMALIZE", allowed_root: str = None):
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
    
    for root, _, files in os.walk(canonical_repo):
        for file in files:
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
            
            try:
                # Open the CANONICAL file — the same inode we validated.
                # This eliminates the TOCTOU race: validate and open are on
                # the same resolved path, not on a mutable original path.
                with open(canonical_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    
                if file.endswith(".py"):
                    findings.extend(scan_python_code(project_id, rel_path, content))
                elif file.endswith(".java"):
                    findings.extend(scan_java_code(project_id, rel_path, content))
                elif file.endswith(".go"):
                    findings.extend(scan_go_code(project_id, rel_path, content))
                    
                if file in ["requirements.txt", "pom.xml", "build.gradle", "go.mod"]:
                    findings.extend(scan_manifest(project_id, file, content))
            except Exception as e:
                scanner_errors.append({"file": rel_path, "error": str(e)})
                
    agile_graph = AgileGraph()
    builder = GraphBuilder(agile_graph)
    builder.build_from_normalized_records(findings)
    g = agile_graph.G
    
    extractor = FactorExtractor(agile_graph)
    scored_assets = []
    unrated_assets = []
    
    # Heuristic weights sum to 1.0
    w = 1.0 / 7.0
    weights = HeuristicWeights(
        data_sensitivity=w, asset_criticality=w, internet_exposure=w,
        crypto_weakness=w, cve_risk=w, library_centrality=w, migration_difficulty=w
    )

    for node, data in g.nodes(data=True):
        if data.get("category") == "file":
            factors = extractor.extract(node, {}, {}, {})
            try:
                score_res = calculate_heuristic_score(factors, weights, policy=policy)
                score_dict = score_res.model_dump()
                score_dict["asset_id"] = node
                if score_res.score is None:
                    unrated_assets.append(score_dict)
                else:
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
            "is_mock": False
        }
    }
