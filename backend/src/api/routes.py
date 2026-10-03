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
from src.dataset.manager import DatasetManager

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
        # Mocking the orchestrator for the endpoint response integration.
        agile_graph = AgileGraph()
        builder = GraphBuilder(agile_graph)
        
        agile_graph.add_node(GraphNode(id="file_1", category="file", properties={}))
        agile_graph.add_node(GraphNode(id="lib_1", category="library", properties={}))
        agile_graph.add_edge(GraphEdge(source_id="file_1", target_id="lib_1", relationship="imports"))
        
        g = agile_graph.G
        
        # In a full scan, we extract factors. Here we mock extracted factors for integration.
        factors = RiskFactors(
            data_sensitivity=FactorValue(value=None, source="mock", confidence=0.0),
            asset_criticality=FactorValue(value=None, source="mock", confidence=0.0),
            internet_exposure=FactorValue(value=None, source="mock", confidence=0.0),
            crypto_weakness=FactorValue(value=None, source="mock", confidence=0.0),
            cve_risk=FactorValue(value=None, source="mock", confidence=0.0),
            library_centrality=FactorValue(value=1.0, source="mock", confidence=1.0),
            migration_difficulty=FactorValue(value=None, source="mock", confidence=0.0)
        )
        weights = HeuristicWeights(
            data_sensitivity=0.2,
            asset_criticality=0.2,
            internet_exposure=0.1,
            crypto_weakness=0.2,
            cve_risk=0.1,
            library_centrality=0.1,
            migration_difficulty=0.1
        )
        score_res = calculate_heuristic_score(factors, weights, policy=MissingDataPolicy.RENORMALIZE)
        
        project_cache[request.project_id] = {
            "graph": g,
            "scores": [
                {
                    "asset_id": "file_1", 
                    "score": score_res.score,
                    "library_centrality": 1.0
                }
            ]
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
