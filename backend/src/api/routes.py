from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import json
import networkx as nx
from src.api.schemas import ScanRequest, ScanResponse, RiskResponse, RiskScore, GraphResponse
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.graph.schema import GraphNode, GraphEdge
from src.risk.heuristic import calculate_heuristic_score
from src.risk.factors import RiskFactors, FactorValue
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.risk.factor_extractor import FactorExtractor
from src.dataset.manager import DatasetManager
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.dependencies.scanner import scan_manifest

router = APIRouter()

# Simple in-memory cache for the dashboard to avoid DB for now
# Maps project_id -> {"graph": nx.MultiDiGraph, "scores": Dict}
project_cache = {}

@router.get("/status")
def get_status():
    return {"status": "ok", "message": "AgileGraph backend is running."}

@router.get("/mosca-index")
def get_mosca_readiness_index(confidentiality: int = 10, migration: int = 5, quantum: int = 20):
    readiness = "Vulnerable" if (confidentiality + migration > quantum) else "Safe"
    return {"readiness": readiness, "c_period": confidentiality, "m_time": migration, "q_horizon": quantum}

@router.post("/scan", response_model=ScanResponse)
def trigger_scan(request: ScanRequest):
    if not os.path.exists(request.repository_path):
        raise HTTPException(status_code=400, detail="Repository path does not exist.")
        
    try:
        findings = []
        for root, _, files in os.walk(request.repository_path):
            for file in files:
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, request.repository_path).replace("\\", "/")
                
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    if file.endswith(".py"):
                        findings.extend(scan_python_code(request.project_id, rel_path, content))
                    elif file.endswith(".java"):
                        findings.extend(scan_java_code(request.project_id, rel_path, content))
                    elif file.endswith(".go"):
                        findings.extend(scan_go_code(request.project_id, rel_path, content))
                        
                    if file in ["requirements.txt", "pom.xml", "build.gradle", "go.mod"]:
                        findings.extend(scan_manifest(request.project_id, file, content))
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
                    score_res = calculate_heuristic_score(factors, weights, policy=MissingDataPolicy.RENORMALIZE)
                    
                    score_dict = score_res.model_dump()
                    score_dict["asset_id"] = node
                    scores.append(score_dict)
                except ValueError:
                    pass

        project_cache[request.project_id] = {
            "graph": g,
            "scores": scores,
            "provenance": {
                "scanned_files": len(findings),
                "is_mock": False
            }
        }
        
        return ScanResponse(
            project_id=request.project_id,
            status="success",
            message="Scan completed successfully.",
            asset_count=len(g.nodes)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/graph", response_model=GraphResponse)
def get_graph(project_id: str):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    g = project_cache[project_id]["graph"]
    data = nx.node_link_data(g)
    
    return GraphResponse(
        project_id=project_id,
        nodes=data.get("nodes", []),
        edges=data.get("edges", [])
    )

@router.get("/projects/{project_id}/risk", response_model=RiskResponse)
def get_risk(project_id: str):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    scores = project_cache[project_id]["scores"]
    
    risk_scores = [RiskScore(**s) for s in scores]
    
    return RiskResponse(
        project_id=project_id,
        assets=risk_scores,
        ml_status="BLOCKED",
        expert_validation_status="BLOCKED"
    )
