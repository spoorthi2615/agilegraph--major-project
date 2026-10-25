from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from src.api.routes import get_project_data
from src.core.storage import default_storage, sanitize_project_id
from src.risk.mosca import calculate_mosca, MoscaResult, MoscaStatus
from src.risk.migration_priority import calculate_migration_priority, MigrationPriorityResult
from src.models.migration_state import RoadmapState, MigrationStateRecord, transition_state
from src.core.auth import User, get_current_user
from src.core.auth_storage import default_auth_storage

router = APIRouter(prefix="/product", tags=["product"])

def verify_project_ownership(project_id: str, username: str, write: bool = False):
    if not default_auth_storage.check_user_owns_project(project_id, username, write=write):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: you do not have permission to {'modify' if write else 'access'} project '{project_id}'."
        )

# In-memory store backed by file storage
roadmap_state_store: Dict[str, Dict[str, MigrationStateRecord]] = {}

def get_project_roadmap(project_id: str) -> Dict[str, MigrationStateRecord]:
    """
    Retrieves roadmap records for project from memory or restores from disk.
    """
    if project_id not in roadmap_state_store:
        try:
            persisted = default_storage.load_roadmap_state(project_id)
            records = {}
            for asset_id, data in persisted.items():
                if isinstance(data, dict):
                    records[asset_id] = MigrationStateRecord(**data)
                elif isinstance(data, MigrationStateRecord):
                    records[asset_id] = data
            roadmap_state_store[project_id] = records
        except Exception:
            roadmap_state_store[project_id] = {}
    return roadmap_state_store[project_id]

class MoscaRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    z: Optional[int] = None

class RoadmapTransitionRequest(BaseModel):
    requested_state: RoadmapState

@router.get("/{project_id}/pqc-readiness")
def get_pqc_readiness(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    result = get_project_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    scores = result["scores"]
    g = result["graph"]
    
    scored_assets = [s for s in scores if s["score"] is not None]
    unrated_assets = [s for s in scores if s["score"] is None]
    
    algorithms = set()
    unknown_algorithms = 0
    for node, data in g.nodes(data=True):
        if data.get("category") == "crypto_usage" or data.get("type") == "CryptoUsageNode":
            props = data.get("properties", data)
            alg = props.get("algorithm") or data.get("algorithm")
            if alg:
                algorithms.add(alg)
                if alg == "unknown":
                    unknown_algorithms += 1
    
    candidates = sum(1 for s in scored_assets if s["score"] >= 0.5)
    
    return {
        "status": "Preliminary heuristic \u2014 initial configurable weights",
        "semantic_disclaimer": "This is an inventory/coverage summary, not a scientifically validated PQC readiness score.",
        "asset_count": len(g.nodes),
        "assessed_assets": len(scored_assets),
        "insufficient_evidence_assets": len(unrated_assets),
        "assets_requiring_attention": candidates,
        "migration_candidates": candidates,
        "recognized_algorithms": list(algorithms - {"unknown"}),
        "unknown_algorithms": unknown_algorithms
    }

@router.post("/mosca", response_model=MoscaResult)
def evaluate_mosca(req: MoscaRequest):
    return calculate_mosca(req.x, req.y, req.z)

@router.get("/{project_id}/assets/{asset_id:path}/priority", response_model=MigrationPriorityResult)
def get_migration_priority(
    project_id: str, 
    asset_id: str, 
    mosca_status: str = "SAFE",
    exposure_posture: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    verify_project_ownership(project_id, current_user.username)
    result = get_project_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    scores = result["scores"]
    g = result["graph"]
    
    if asset_id not in g:
        raise HTTPException(status_code=404, detail="Asset not found.")
        
    asset_score = next((s for s in scores if s["asset_id"] == asset_id), None)
    if not asset_score:
        base_risk = None
        missing_factors = []
        migration_difficulty = None
    else:
        base_risk = asset_score["score"]
        missing_factors = asset_score.get("missing_factors", [])
        factors = asset_score.get("factors", {})
        migration_difficulty = factors.get("migration_difficulty", {}).get("value")
        
    node_data = g.nodes[asset_id]
    algorithm = node_data.get("algorithm") if node_data.get("type") == "CryptoUsageNode" or node_data.get("category") == "crypto_usage" else None
    effective_exposure = exposure_posture or node_data.get("network_exposure")
    
    try:
        mosca_enum = MoscaStatus(mosca_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Mosca status provided.")
        
    return calculate_migration_priority(
        asset_id=asset_id,
        base_risk=base_risk,
        mosca_status=mosca_enum,
        missing_factors=missing_factors,
        exposure_posture=effective_exposure,
        migration_difficulty=migration_difficulty,
        algorithm=algorithm
    )

@router.get("/{project_id}/assets/{asset_id:path}/roadmap", response_model=MigrationStateRecord)
def get_roadmap_state(project_id: str, asset_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    result = get_project_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
        
    g = result["graph"]
    if asset_id not in g:
        raise HTTPException(status_code=404, detail="Asset not found.")
        
    project_roadmap = get_project_roadmap(project_id)
    if asset_id not in project_roadmap:
        project_roadmap[asset_id] = MigrationStateRecord(asset_id=asset_id)
        default_storage.save_roadmap_state(project_id, project_roadmap)
        
    return project_roadmap[asset_id]

@router.post("/{project_id}/assets/{asset_id:path}/roadmap", response_model=MigrationStateRecord)
def transition_roadmap_state(project_id: str, asset_id: str, req: RoadmapTransitionRequest, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username, write=True)
    result = get_project_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
        
    g = result["graph"]
    if asset_id not in g:
        raise HTTPException(status_code=404, detail="Asset not found.")
        
    project_roadmap = get_project_roadmap(project_id)
    if asset_id not in project_roadmap:
        project_roadmap[asset_id] = MigrationStateRecord(asset_id=asset_id)
        
    current_record = project_roadmap[asset_id]
    
    try:
        new_record = transition_state(current_record, req.requested_state)
        project_roadmap[asset_id] = new_record
        default_storage.save_roadmap_state(project_id, project_roadmap)
        return new_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/crypto-inventory")
def get_crypto_inventory(project_id: str, current_user: User = Depends(get_current_user)):
    verify_project_ownership(project_id, current_user.username)
    result = get_project_data(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    g = result["graph"]
    scores = result["scores"]
    
    # Map score by asset_id
    score_map = {s["asset_id"]: s for s in scores}
    
    items = []
    languages = set()
    algorithms = set()
    libraries = set()
    
    for node, data in g.nodes(data=True):
        if data.get("category") == "crypto_usage" or data.get("type") == "CryptoUsageNode":
            asset_id = str(node)
            props = data.get("properties", data)
            
            lang = props.get("language")
            alg = props.get("algorithm")
            op = props.get("operation")
            lib = props.get("library")
            source = f"{props.get('file', 'Unknown')}:{props.get('line', '?')}" if props.get("file") else "Unknown"
            
            if lang: languages.add(lang)
            if alg and alg != "unknown": algorithms.add(alg)
            if lib: libraries.add(lib)
            
            asset_score = score_map.get(asset_id)
            risk = asset_score["score"] if asset_score else None
            evidence = "Missing data" if asset_score and asset_score.get("score") is None else "Assessed"
            
            items.append({
                "asset_id": asset_id,
                "language": lang,
                "algorithm": alg,
                "operation": op,
                "library": lib,
                "source": source,
                "evidence_status": evidence,
                "risk": risk
            })
            
    return {
        "project_id": project_id,
        "summary": {
            "total_assets": len(g.nodes),
            "crypto_usages": len(items),
            "languages": len(languages),
            "algorithms": len(algorithms),
            "libraries": len(libraries)
        },
        "items": items,
        "coverage": {
            "certificates": "NOT_COLLECTED",
            "endpoints": "NOT_COLLECTED",
            "sensitive_data": "NOT_COLLECTED"
        }
    }
