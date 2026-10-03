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

def extract_node_features(properties: dict, config: FeatureConfig) -> torch.Tensor:
    """
    Extracts the 7 context factors and their missingness masks into a feature tensor.
    CRITICAL: base_risk is strictly excluded unless include_base_risk=True
    """
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
    if heuristic_info:
        return TargetLabel(
            class_idx=heuristic_info.get("class_idx"),
            source=LabelSource.HEURISTIC,
            confidence=heuristic_info.get("confidence", 0.5)
        )
        
    return TargetLabel(class_idx=None, source=LabelSource.UNKNOWN, confidence=0.0)
