from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from src.api.routes import project_cache
from src.risk.mosca import calculate_mosca, MoscaResult, MoscaStatus
from src.risk.migration_priority import calculate_migration_priority, MigrationPriorityResult
from src.models.migration_state import RoadmapState, MigrationStateRecord, transition_state

router = APIRouter(prefix="/product", tags=["product"])

# In-memory store for roadmap state
roadmap_state_store: Dict[str, Dict[str, MigrationStateRecord]] = {}

class MoscaRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    z: Optional[int] = None

class RoadmapTransitionRequest(BaseModel):
    requested_state: RoadmapState

@router.get("/{project_id}/pqc-readiness")
def get_pqc_readiness(project_id: str):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    result = project_cache[project_id]
    scores = result["scores"]
    g = result["graph"]
    
    scored_assets = [s for s in scores if s["score"] is not None]
    unrated_assets = [s for s in scores if s["score"] is None]
    
    algorithms = set()
    unknown_algorithms = 0
    for node, data in g.nodes(data=True):
        if data.get("type") == "CryptoUsageNode":
            alg = data.get("algorithm")
            if alg:
                algorithms.add(alg)
                if alg == "unknown":
                    unknown_algorithms += 1
    
    candidates = sum(1 for s in scored_assets if s["score"] >= 0.5)
    
    return {
        "status": "Preliminary heuristic \u2014 expert validation pending",
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
def get_migration_priority(project_id: str, asset_id: str, mosca_status: str = "NOT_AT_RISK"):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
    
    scores = project_cache[project_id]["scores"]
    g = project_cache[project_id]["graph"]
    
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
        
    algorithm = g.nodes[asset_id].get("algorithm") if g.nodes[asset_id].get("type") == "CryptoUsageNode" else None
    
    try:
        mosca_enum = MoscaStatus(mosca_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Mosca status provided.")
        
    return calculate_migration_priority(
        asset_id=asset_id,
        base_risk=base_risk,
        mosca_status=mosca_enum,
        missing_factors=missing_factors,
        migration_difficulty=migration_difficulty,
        algorithm=algorithm
    )

@router.get("/{project_id}/assets/{asset_id:path}/roadmap", response_model=MigrationStateRecord)
def get_roadmap_state(project_id: str, asset_id: str):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
        
    g = project_cache[project_id]["graph"]
    if asset_id not in g:
        raise HTTPException(status_code=404, detail="Asset not found.")
        
    if project_id not in roadmap_state_store:
        roadmap_state_store[project_id] = {}
        
    if asset_id not in roadmap_state_store[project_id]:
        roadmap_state_store[project_id][asset_id] = MigrationStateRecord(asset_id=asset_id)
        
    return roadmap_state_store[project_id][asset_id]

@router.post("/{project_id}/assets/{asset_id:path}/roadmap", response_model=MigrationStateRecord)
def transition_roadmap_state(project_id: str, asset_id: str, req: RoadmapTransitionRequest):
    if project_id not in project_cache:
        raise HTTPException(status_code=404, detail="Project not found or not scanned.")
        
    g = project_cache[project_id]["graph"]
    if asset_id not in g:
        raise HTTPException(status_code=404, detail="Asset not found.")
        
    if project_id not in roadmap_state_store:
        roadmap_state_store[project_id] = {}
        
    if asset_id not in roadmap_state_store[project_id]:
        roadmap_state_store[project_id][asset_id] = MigrationStateRecord(asset_id=asset_id)
        
    current_record = roadmap_state_store[project_id][asset_id]
    
    try:
        new_record = transition_state(current_record, req.requested_state)
        roadmap_state_store[project_id][asset_id] = new_record
        return new_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
