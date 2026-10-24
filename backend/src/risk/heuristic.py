from typing import List, Dict, Tuple, Optional
from src.risk.factors import RiskFactors
from src.risk.weights import HeuristicWeights
from src.risk.score import RiskScoreResult, MissingDataPolicy, FactorContribution

CURRENT_FORMULA_VERSION = "heuristic-v1.0"


def calculate_heuristic_score(
    factors: RiskFactors, 
    weights: Optional[HeuristicWeights] = None, 
    policy: MissingDataPolicy = MissingDataPolicy.RENORMALIZE
) -> RiskScoreResult:
    """
    Calculates the 7-factor composite heuristic risk score in [0.0, 1.0].
    
    Supports two explicit missing-evidence policies:
      - RENORMALIZE: Reweights valid factors proportionally across observed evidence.
      - CONSERVATIVE: Assigns maximum penalty risk (1.0) to missing/unobserved evidence.
      - STRICT: Rejects calculation if any factor is unobserved.
    """
    active_weights = weights if weights is not None else HeuristicWeights()
    
    factors_dict = factors.model_dump()
    weights_dict = active_weights.model_dump()
    
    missing_factors = []
    valid_factors = {}
    
    for factor_name, fv in factors_dict.items():
        if fv["value"] is None:
            missing_factors.append(factor_name)
        else:
            # Validate bounds
            val = float(fv["value"])
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Factor {factor_name} out of bounds: {val}")
            valid_factors[factor_name] = val
            
    if policy == MissingDataPolicy.STRICT and len(missing_factors) > 0:
        raise ValueError(f"STRICT policy violation. Missing factors: {missing_factors}")
        
    available_weight = sum(weights_dict[f] for f in valid_factors.keys())
    
    if available_weight == 0.0:
        if policy == MissingDataPolicy.CONSERVATIVE:
            # All factors missing under conservative policy -> score = 1.0
            contributions = {
                f: FactorContribution(value=1.0, weight=weights_dict[f], contribution=weights_dict[f])
                for f in missing_factors
            }
            return RiskScoreResult(
                score=1.0,
                scale="0.0-1.0",
                formula_version=CURRENT_FORMULA_VERSION,
                weights=weights_dict,
                factors=factors_dict,
                weighted_contributions=contributions,
                missing_factors=missing_factors,
                missing_data_policy=policy,
                assumptions=["Conservative policy: all factors unobserved, maximum risk (1.0) applied."]
            )
        else:
            # Cannot calculate score with no observed factors under renormalize
            return RiskScoreResult(
                score=None,
                scale="0.0-1.0",
                formula_version=CURRENT_FORMULA_VERSION,
                weights=weights_dict,
                factors=factors_dict,
                weighted_contributions={},
                missing_factors=missing_factors,
                missing_data_policy=policy,
                assumptions=["Unscored due to missing factors (0.0 valid weight)"]
            )
        
    score = 0.0
    contributions = {}
    
    if policy == MissingDataPolicy.RENORMALIZE:
        for factor_name, val in valid_factors.items():
            w = weights_dict[factor_name]
            effective_weight = w / available_weight
            contrib = val * effective_weight
            score += contrib
            contributions[factor_name] = FactorContribution(
                value=val,
                weight=effective_weight,
                contribution=contrib
            )
    elif policy == MissingDataPolicy.CONSERVATIVE:
        for factor_name, val in valid_factors.items():
            w = weights_dict[factor_name]
            contrib = val * w
            score += contrib
            contributions[factor_name] = FactorContribution(
                value=val,
                weight=w,
                contribution=contrib
            )
        for factor_name in missing_factors:
            w = weights_dict[factor_name]
            contrib = 1.0 * w  # Worst-case penalty
            score += contrib
            contributions[factor_name] = FactorContribution(
                value=1.0,
                weight=w,
                contribution=contrib
            )
    else:  # STRICT
        for factor_name, val in valid_factors.items():
            w = weights_dict[factor_name]
            contrib = val * w
            score += contrib
            contributions[factor_name] = FactorContribution(
                value=val,
                weight=w,
                contribution=contrib
            )
            
    # Guarantee score is bounded in [0.0, 1.0]
    bounded_score = min(max(score, 0.0), 1.0)
    
    assumptions = [
        "AgileGraph Deterministic Heuristic Risk Score",
        "Operational prioritization estimate (not predictive ground truth)"
    ]
    if len(valid_factors) < len(factors_dict):
        assumptions.append(f"PRELIMINARY: {len(valid_factors)}/{len(factors_dict)} factors computed. Missing: {missing_factors}")
        
    if policy == MissingDataPolicy.RENORMALIZE and missing_factors:
        assumptions.append(f"Renormalized over observed weight ({available_weight:.2f})")
    elif policy == MissingDataPolicy.CONSERVATIVE and missing_factors:
        assumptions.append(f"Conservative penalty applied to missing factors: {missing_factors}")
        
    return RiskScoreResult(
        score=bounded_score,
        scale="0.0-1.0",
        formula_version=CURRENT_FORMULA_VERSION,
        weights=weights_dict,
        factors=factors_dict,
        weighted_contributions=contributions,
        missing_factors=missing_factors,
        missing_data_policy=policy,
        assumptions=assumptions
    )


def rank_assets(assets: Dict[str, RiskScoreResult]) -> List[Tuple[int, str, Optional[float]]]:
    """
    Deterministically ranks assets by score (descending), breaking ties by asset_id (ascending).
    Returns list of (rank, asset_id, base_risk)
    """
    sorted_items = sorted(
        assets.items(), 
        key=lambda item: (-item[1].score if item[1].score is not None else 1.0, item[0])
    )
    
    ranking = []
    for rank, (asset_id, result) in enumerate(sorted_items, start=1):
        ranking.append((rank, asset_id, result.score))
        
    return ranking
