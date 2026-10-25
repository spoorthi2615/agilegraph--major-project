from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum
import torch

class LabelSource(str, Enum):
    EXPERT = "EXPERT"
    SYNTHETIC = "SYNTHETIC"
    HEURISTIC = "HEURISTIC"
    UNKNOWN = "UNKNOWN"

class TargetLabel(BaseModel):
    # E.g., High (2), Medium (1), Low (0)
    class_idx: Optional[int]
    source: LabelSource
    confidence: float

class FeatureConfig(BaseModel):
    include_base_risk: bool = False
    structure_only: bool = False

def extract_node_features(properties: dict, config: FeatureConfig) -> torch.Tensor:
    """
    Extracts the 7 context factors and their missingness masks into a feature tensor.
    CRITICAL: If structure_only=True, strictly NO semantic properties or risks are included.
    CRITICAL: base_risk is strictly excluded unless include_base_risk=True
    """
    if config.structure_only:
        # Strict ablation: no algorithm, no risk, no heuristic.
        # Just return a dummy feature so the GNN can learn from topology/node-types.
        return torch.zeros(1, dtype=torch.float)

    factors = properties.get("risk_factors", {})
    keys = [
        "data_sensitivity", "asset_criticality", "internet_exposure", 
        "crypto_weakness", "cve_risk", "library_centrality", "migration_difficulty"
    ]
    
    feat_list = []
    missing_list = []
    
    for k in keys:
        val = factors.get(k)
        if val is not None:
            feat_list.append(float(val))
            missing_list.append(0.0)
        else:
            feat_list.append(0.0)
            missing_list.append(1.0) # Explicit missingness mask
    
    if config.include_base_risk:
        base_risk = properties.get("base_risk")
        if base_risk is not None:
            feat_list.append(float(base_risk))
            missing_list.append(0.0)
        else:
            feat_list.append(0.0)
            missing_list.append(1.0)
            
    # Concatenate features and their corresponding missingness masks
    return torch.tensor(feat_list + missing_list, dtype=torch.float)


def derive_heuristic_label(
    score: Optional[float], 
    low_threshold: float = 0.30, 
    high_threshold: float = 0.60
) -> Optional[dict]:
    """
    Derives a weak-supervision 3-class target label from a continuous heuristic risk score.
    Classes:
      - 0 (LOW): score < low_threshold
      - 1 (MEDIUM): low_threshold <= score < high_threshold
      - 2 (HIGH): score >= high_threshold
    
    Returns a dictionary suitable for 'heuristic_label' properties:
      {'class_idx': int, 'confidence': float}
    Returns None if the score is None or invalid, preserving missing/unrated data.
    """
    if score is None:
        return None
    try:
        val = float(score)
    except (TypeError, ValueError):
        return None

    if not (0.0 <= val <= 1.0):
        return None

    if val < low_threshold:
        class_idx = 0
    elif val < high_threshold:
        class_idx = 1
    else:
        class_idx = 2

    return {
        "class_idx": class_idx,
        "confidence": 0.5
    }


def extract_target_label(properties: dict) -> TargetLabel:
    """
    Extracts the target label and explicitly tracks its provenance.
    If no label is present, it returns an UNKNOWN source without fabricating one.
    """
    label_info = properties.get("expert_label")
    if label_info:
        return TargetLabel(
            class_idx=label_info.get("class_idx"),
            source=LabelSource.EXPERT,
            confidence=label_info.get("confidence", 1.0)
        )
        
    # Check for heuristic label (weak supervision)
    heuristic_info = properties.get("heuristic_label")
    if heuristic_info and heuristic_info.get("class_idx") is not None:
        return TargetLabel(
            class_idx=int(heuristic_info.get("class_idx")),
            source=LabelSource.HEURISTIC,
            confidence=float(heuristic_info.get("confidence", 0.5))
        )
        
    return TargetLabel(class_idx=None, source=LabelSource.UNKNOWN, confidence=0.0)
