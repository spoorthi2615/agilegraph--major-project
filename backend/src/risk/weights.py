from pydantic import BaseModel, Field, model_validator
import math

class HeuristicWeights(BaseModel):
    """
    INITIAL / CONFIGURABLE WEIGHTS
    NOT EXPERT-VALIDATED
    """
    data_sensitivity: float = Field(..., ge=0.0, le=1.0)
    asset_criticality: float = Field(..., ge=0.0, le=1.0)
    internet_exposure: float = Field(..., ge=0.0, le=1.0)
    crypto_weakness: float = Field(..., ge=0.0, le=1.0)
    cve_risk: float = Field(..., ge=0.0, le=1.0)
    library_centrality: float = Field(..., ge=0.0, le=1.0)
    migration_difficulty: float = Field(..., ge=0.0, le=1.0)

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

def perturb_weights(baseline: HeuristicWeights, perturbation: float = 0.10) -> HeuristicWeights:
    """
    Sensitivity analysis interface for the eventual ±10-20% study.
    Returns a new normalized set of weights with the specified perturbation
    applied to the crypto_weakness (for instance), renormalizing the rest.
    """
    # For a simple deterministic perturbation interface:
    # Perturb the first factor up by `perturbation`, distribute remaining to others.
    # The actual scientific permutation strategy will be implemented later.
    raw_dict = baseline.model_dump()
    num_factors = len(raw_dict)
    
    # We'll just shift one arbitrarily to prove the interface
    target_key = "crypto_weakness"
    new_val = min(raw_dict[target_key] + perturbation, 1.0)
    diff = new_val - raw_dict[target_key]
    
    # Adjust others equally
    adjustment_per_other = diff / (num_factors - 1)
    
    new_dict = {}
    for k, v in raw_dict.items():
        if k == target_key:
            new_dict[k] = new_val
        else:
            new_dict[k] = max(v - adjustment_per_other, 0.0)
            
    # Normalize mathematically to ensure sum == 1.0
    new_total = sum(new_dict.values())
    for k in new_dict:
        new_dict[k] = new_dict[k] / new_total
        
    return HeuristicWeights(**new_dict)
