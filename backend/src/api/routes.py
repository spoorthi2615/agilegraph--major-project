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
from src.pipeline.runner import run_pipeline

router = APIRouter()

# Simple in-memory cache for the dashboard to avoid DB for now
# Maps project_id -> {"graph": nx.MultiDiGraph, "scores": Dict}
project_cache = {}

@router.get("/status")
def get_status():
    return {"status": "ok", "message": "AgileGraph backend is running."}

@router.get("/mosca-index")
def get_mosca_readiness_index(confidentiality: int = 10, migration: int = 5, quantum: int = 20):
    if confidentiality < 0 or migration < 0 or quantum < 0:
        raise HTTPException(status_code=400, detail="Mosca parameters must be non-negative.")
    readiness = "Vulnerable" if (confidentiality + migration > quantum) else "Safe"
    return {"readiness": readiness, "c_period": confidentiality, "m_time": migration, "q_horizon": quantum}

@router.post("/scan", response_model=ScanResponse)
def trigger_scan(request: ScanRequest):
    repo_path = request.repository_path.strip().strip('"').strip("'")
    if repo_path.startswith("http://") or repo_path.startswith("https://") or "github.com" in repo_path:
        raise HTTPException(status_code=400, detail="The AgileGraph scanner requires a local filesystem path, not a remote URL. The current architecture does not clone remote repositories.")
    if repo_path.startswith("file:///"):
        repo_path = repo_path[8:]
    elif repo_path.startswith("file://"):
        repo_path = repo_path[7:]

    if not os.path.exists(repo_path):
        raise HTTPException(status_code=400, detail="Repository path does not exist.")
        
    allowed_root_env = os.environ.get("AGILEGRAPH_SCAN_ROOT")
    allowed_root = os.path.realpath(allowed_root_env) if allowed_root_env else None
    
    req_root = os.path.realpath(repo_path)
    
    try:
        result = run_pipeline(req_root, request.project_id, "RENORMALIZE", allowed_root=allowed_root)
        project_cache[request.project_id] = result
        prov = result["provenance"]
        
        return ScanResponse(
            project_id=request.project_id,
            status="success",
            message="Scan completed successfully.",
            asset_count=len(result["graph"].nodes),
            scored_assets=prov.get("scored_assets", 0),
            unrated_assets=prov.get("unrated_assets", 0),
            skipped_files=prov.get("skipped_files", 0),
        )
    except ValueError as e:
        if "outside allowed scan root" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
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
