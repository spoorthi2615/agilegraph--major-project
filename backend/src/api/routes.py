from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
import tempfile
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
from src.core.storage import default_storage, sanitize_project_id
from src.core.auth import User, get_current_user
from src.core.auth_storage import default_auth_storage

router = APIRouter()

# In-memory working cache backed by persistent file storage
project_cache = {}

def get_project_data(project_id: str):
    """
    Retrieves project scan data from in-memory cache or restores from disk storage.
    """
    if project_id in project_cache:
        return project_cache[project_id]
        
    try:
        loaded = default_storage.load_scan_result(project_id)
        if loaded:
            project_cache[project_id] = loaded
            return loaded
    except ValueError:
        pass
    return None

def verify_project_ownership(project_id: str, username: str, write: bool = False):
    if not default_auth_storage.check_user_owns_project(project_id, username, write=write):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: you do not have permission to {'modify' if write else 'access'} project '{project_id}'."
        )

def verify_project_scan_permission(project_id: str, username: str):
    """
    Ensure user has authorization to scan or re-scan this project_id.
    - If project is owned by another user: reject with 403.
    - If project is a shared benchmark project: reject with 403 unless in test mode.
    - If project exists on disk without an owner: reject with 403 (unowned projects cannot be claimed).
    - If project does not exist yet, or is owned by user: permit scan.
    """
    clean_user = username.strip().lower()
    clean_proj = project_id.strip()
    owner = default_auth_storage.get_project_owner(clean_proj)
    
    if owner is not None and owner != clean_user:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: project '{project_id}' is owned by another user."
        )
        
    from src.core.auth_storage import LEGACY_BENCHMARK_PROJECTS
    if clean_proj in LEGACY_BENCHMARK_PROJECTS:
        from src.core.auth import is_anonymous_allowed
        if not is_anonymous_allowed():
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: cannot overwrite shared research benchmark project '{project_id}'."
            )
            
    if owner is None and default_storage.project_exists(clean_proj) and clean_proj not in LEGACY_BENCHMARK_PROJECTS:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: project '{project_id}' exists without assigned ownership. Unowned projects cannot be claimed."
        )

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
def trigger_scan(request: ScanRequest, current_user: User = Depends(get_current_user)):
    repo_path = request.repository_path.strip().strip('"').strip("'")
    if repo_path.startswith("http://") or repo_path.startswith("https://") or "github.com" in repo_path:
        raise HTTPException(status_code=400, detail="The AgileGraph scanner requires a local filesystem path, not a remote URL. The current architecture does not clone remote repositories.")
    if repo_path.startswith("file:///"):
        repo_path = repo_path[8:]
    elif repo_path.startswith("file://"):
        repo_path = repo_path[7:]

    if not os.path.exists(repo_path):
        raise HTTPException(status_code=400, detail="Repository path does not exist.")
        
    allowed_root_env = os.environ.get("AGILEGRAPH_SCAN_ROOT") or os.environ.get("ALLOWED_SCAN_ROOT")
    allowed_root = os.path.realpath(allowed_root_env) if allowed_root_env else None
    
    req_root = os.path.realpath(repo_path)
    
    try:
        # Validate project_id for safety
        sanitize_project_id(request.project_id)
        
        # Verify scan permission and ownership
        verify_project_scan_permission(request.project_id, current_user.username)
        
        result = run_pipeline(req_root, request.project_id, "RENORMALIZE", allowed_root=allowed_root)
        project_cache[request.project_id] = result
        default_storage.save_scan_result(request.project_id, result)
        default_auth_storage.assign_project_owner(request.project_id, current_user.username)
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
    except HTTPException:
        raise
    except ValueError as e:
        if "outside allowed scan root" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/graph", response_model=GraphResponse)
def get_graph(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    data_dict = get_project_data(project_id)
    if not data_dict:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    g = data_dict["graph"]
    data = nx.node_link_data(g)
    
    return GraphResponse(
        project_id=project_id,
        nodes=data.get("nodes", []),
        edges=data.get("edges", [])
    )

@router.get("/projects/{project_id}/risk", response_model=RiskResponse)
def get_risk(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    data_dict = get_project_data(project_id)
    if not data_dict:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    scores = data_dict["scores"]
    
    risk_scores = [RiskScore(**s) for s in scores]
    
    return RiskResponse(
        project_id=project_id,
        assets=risk_scores,
        ml_status="ARCHITECTURAL_PROTOTYPE"
    )

@router.get("/projects/{project_id}/report/json")
def export_report_json(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    data_dict = get_project_data(project_id)
    if not data_dict:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    from src.pipeline.reporter import build_export_payload
    return build_export_payload(project_id, data_dict)

@router.get("/projects/{project_id}/report/markdown", response_class=PlainTextResponse)
def export_report_markdown(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    data_dict = get_project_data(project_id)
    if not data_dict:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    from src.pipeline.reporter import generate_markdown_report
    with tempfile.TemporaryDirectory() as td:
        json_path = os.path.join(td, "scan.json")
        md_path = os.path.join(td, "report.md")
        g_data = nx.node_link_data(data_dict["graph"])
        payload = {
            "project_id": project_id,
            "analysis_type": "HEURISTIC",
            "ml_status": "ARCHITECTURAL_PROTOTYPE",
            "missing_data_policy": data_dict.get("missing_data_policy", "RENORMALIZE"),
            "provenance": data_dict.get("provenance", {}),
            "assets": data_dict.get("scores", []),
            "graph": g_data
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        generate_markdown_report(json_path, md_path)
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()

@router.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a project and its associated artifacts.
    Requires project ownership (write permission).
    """
    sanitize_project_id(project_id)
    verify_project_ownership(project_id, current_user.username, write=True)
    
    exists = default_storage.project_exists(project_id) or project_id in project_cache
    if not exists:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    project_cache.pop(project_id, None)
    default_storage.delete_project(project_id)
    default_auth_storage.delete_project_owner(project_id)
    
    return {"status": "success", "message": f"Project '{project_id}' deleted successfully."}

