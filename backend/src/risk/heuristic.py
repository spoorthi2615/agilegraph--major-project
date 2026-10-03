from typing import List, Dict, Tuple
from src.risk.factors import RiskFactors
from src.risk.weights import HeuristicWeights
from src.risk.score import RiskScoreResult, MissingDataPolicy, FactorContribution

CURRENT_FORMULA_VERSION = "heuristic-v0.1"

def calculate_heuristic_score(
    factors: RiskFactors, 
    weights: HeuristicWeights, 
    policy: MissingDataPolicy = MissingDataPolicy.STRICT
) -> RiskScoreResult:
    
    factors_dict = factors.model_dump()
    weights_dict = weights.model_dump()
    
    missing_factors = []
    valid_factors = {}
    
    for factor_name, fv in factors_dict.items():
        if fv["value"] is None:
            missing_factors.append(factor_name)
        else:
            # Validate bounds
            if not (0.0 <= fv["value"] <= 1.0):
                raise ValueError(f"Factor {factor_name} out of bounds: {fv['value']}")
            valid_factors[factor_name] = fv["value"]
            
    if policy == MissingDataPolicy.STRICT and len(missing_factors) > 0:
        raise ValueError(f"STRICT policy violation. Missing factors: {missing_factors}")
        
    # Renormalize weights if needed
    available_weight = sum(weights_dict[f] for f in valid_factors.keys())
    
    if available_weight == 0.0:
        # Cannot calculate score with no factors
        raise ValueError("Cannot calculate score: no valid factors available.")
        
    score = 0.0
    contributions = {}
    
    for factor_name, val in valid_factors.items():
        w = weights_dict[factor_name]
        if policy == MissingDataPolicy.RENORMALIZE:
            effective_weight = w / available_weight
        else:
            effective_weight = w
            
        contrib = val * effective_weight
        score += contrib
        
        contributions[factor_name] = FactorContribution(
            value=val,
            weight=effective_weight,
            contribution=contrib
        )
        
    assumptions = [
        "Initial AgileGraph Heuristic Risk Score - NOT EXPERT-VALIDATED",
        "Acts as weak supervision signal, not ground truth"
    ]
    if policy == MissingDataPolicy.RENORMALIZE and missing_factors:
        assumptions.append(f"Renormalized due to missing factors: {missing_factors}")
        
    return RiskScoreResult(
        score=score,
        formula_version=CURRENT_FORMULA_VERSION,
        weights=weights_dict,
        factors=factors_dict,
        weighted_contributions=contributions,
        missing_factors=missing_factors,
        missing_data_policy=policy,
        assumptions=assumptions
    )

def rank_assets(assets: Dict[str, RiskScoreResult]) -> List[Tuple[int, str, float]]:
    """
    Deterministically ranks assets by score (descending), breaking ties by asset_id (ascending).
    Returns list of (rank, asset_id, base_risk)
    """
    sorted_items = sorted(assets.items(), key=lambda item: (-item[1].score, item[0]))
    
    ranking = []
    for rank, (asset_id, result) in enumerate(sorted_items, start=1):
        ranking.append((rank, asset_id, result.score))
        
    return ranking
