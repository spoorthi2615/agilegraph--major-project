import os
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

def run_pipeline(repository_path: str, project_id: str, missing_data_policy: str = "RENORMALIZE"):
    if not os.path.exists(repository_path):
        raise ValueError("Repository path does not exist.")
        
    policy = MissingDataPolicy(missing_data_policy)
        
    findings = []
    for root, _, files in os.walk(repository_path):
        for file in files:
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, repository_path).replace("\\", "/")
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                if file.endswith(".py"):
                    findings.extend(scan_python_code(project_id, rel_path, content))
                elif file.endswith(".java"):
                    findings.extend(scan_java_code(project_id, rel_path, content))
                elif file.endswith(".go"):
                    findings.extend(scan_go_code(project_id, rel_path, content))
                    
                if file in ["requirements.txt", "pom.xml", "build.gradle", "go.mod"]:
                    findings.extend(scan_manifest(project_id, file, content))
            except Exception:
                pass
                
    agile_graph = AgileGraph()
    builder = GraphBuilder(agile_graph)
    builder.build_from_normalized_records(findings)
    g = agile_graph.G
    
    extractor = FactorExtractor(agile_graph)
    scores = []
    
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
                scores.append(score_dict)
            except ValueError:
                pass

    return {
        "graph": g,
        "scores": scores,
        "provenance": {
            "scanned_files": len(findings),
            "is_mock": False
        }
    }
