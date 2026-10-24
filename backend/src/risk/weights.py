import os
import json
import math
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional

DEFAULT_CONFIG_PATH = os.path.realpath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "heuristic_weights.json")
)

# Canonical default weights matching heuristic_weights.json (sum == 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "crypto_weakness": 0.25,
    "asset_criticality": 0.15,
    "data_sensitivity": 0.15,
    "internet_exposure": 0.15,
    "migration_difficulty": 0.10,
    "library_centrality": 0.10,
    "cve_risk": 0.10,
}


class HeuristicWeights(BaseModel):
    """
    Seven-factor heuristic risk weights configuration for AgileGraph.
    Weights sum strictly to 1.0. All values are within [0.0, 1.0].
    """
    crypto_weakness: float = Field(default=DEFAULT_WEIGHTS["crypto_weakness"], ge=0.0, le=1.0)
    asset_criticality: float = Field(default=DEFAULT_WEIGHTS["asset_criticality"], ge=0.0, le=1.0)
    data_sensitivity: float = Field(default=DEFAULT_WEIGHTS["data_sensitivity"], ge=0.0, le=1.0)
    internet_exposure: float = Field(default=DEFAULT_WEIGHTS["internet_exposure"], ge=0.0, le=1.0)
    migration_difficulty: float = Field(default=DEFAULT_WEIGHTS["migration_difficulty"], ge=0.0, le=1.0)
    library_centrality: float = Field(default=DEFAULT_WEIGHTS["library_centrality"], ge=0.0, le=1.0)
    cve_risk: float = Field(default=DEFAULT_WEIGHTS["cve_risk"], ge=0.0, le=1.0)

    @model_validator(mode='after')
    def validate_sum(self) -> 'HeuristicWeights':
        total = (
            self.data_sensitivity +
            self.asset_criticality +
            self.internet_exposure +
            self.crypto_weakness +
            self.cve_risk +
            self.library_centrality +
            self.migration_difficulty
        )
        if not math.isclose(total, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self

    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> 'HeuristicWeights':
        path = config_path or DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            weights_data = data.get("weights", {})
            parsed = {}
            for k, v in weights_data.items():
                parsed[k] = v.get("weight") if isinstance(v, dict) else v
            return cls(**parsed)
        return cls()


def perturb_weights(baseline: HeuristicWeights, target_key: str = "crypto_weakness", perturbation: float = 0.10) -> HeuristicWeights:
    """
    Perturbs a single target factor weight by delta and proportionally renormalizes others.
    """
    raw_dict = baseline.model_dump()
    num_factors = len(raw_dict)
    
    new_val = min(max(raw_dict[target_key] + perturbation, 0.0), 1.0)
    diff = new_val - raw_dict[target_key]
    
    adjustment_per_other = diff / (num_factors - 1)
    
    new_dict = {}
    for k, v in raw_dict.items():
        if k == target_key:
            new_dict[k] = new_val
        else:
            new_dict[k] = max(v - adjustment_per_other, 0.0)
            
    # Proportional simplex renormalization
    new_total = sum(new_dict.values())
    for k in new_dict:
        new_dict[k] = new_dict[k] / new_total
        
    return HeuristicWeights(**new_dict)
