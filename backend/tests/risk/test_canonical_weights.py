import os
import math
import pytest
from src.risk.weights import HeuristicWeights, DEFAULT_WEIGHTS
from src.risk.factors import RiskFactors, FactorValue
from src.risk.heuristic import calculate_heuristic_score
from src.risk.score import MissingDataPolicy


def test_canonical_weights_from_config():
    """Verifies that HeuristicWeights.from_config() loads canonical weights summing strictly to 1.0."""
    w = HeuristicWeights.from_config()
    assert math.isclose(w.crypto_weakness, 0.25, rel_tol=1e-5)
    assert math.isclose(w.asset_criticality, 0.15, rel_tol=1e-5)
    assert math.isclose(w.data_sensitivity, 0.15, rel_tol=1e-5)
    assert math.isclose(w.internet_exposure, 0.15, rel_tol=1e-5)
    assert math.isclose(w.migration_difficulty, 0.10, rel_tol=1e-5)
    assert math.isclose(w.library_centrality, 0.10, rel_tol=1e-5)
    assert math.isclose(w.cve_risk, 0.10, rel_tol=1e-5)
    
    total = sum(w.model_dump().values())
    assert math.isclose(total, 1.0, rel_tol=1e-5)


def test_weight_change_affects_score():
    """Verifies that altering a weight changes the computed risk score proportionally."""
    factors = RiskFactors(
        data_sensitivity=FactorValue(value=0.0, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.0, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.0, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=1.0, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.0, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.0, source="test", confidence=1.0)
    )
    
    # Under canonical weights, crypto_weakness=0.25, all others 0.0 -> score = 0.25
    canonical_w = HeuristicWeights.from_config()
    res1 = calculate_heuristic_score(factors, canonical_w, policy=MissingDataPolicy.RENORMALIZE)
    assert math.isclose(res1.score, 0.25, rel_tol=1e-4)
    
    # Custom weights with crypto_weakness=0.40, others adjusted
    custom_w = HeuristicWeights(
        crypto_weakness=0.40,
        asset_criticality=0.10,
        data_sensitivity=0.10,
        internet_exposure=0.10,
        migration_difficulty=0.10,
        library_centrality=0.10,
        cve_risk=0.10
    )
    res2 = calculate_heuristic_score(factors, custom_w, policy=MissingDataPolicy.RENORMALIZE)
    assert math.isclose(res2.score, 0.40, rel_tol=1e-4)
    assert res2.score > res1.score


def test_scores_remain_bounded():
    """Verifies that scores remain within [0.0, 1.0] under extreme factors and canonical weights."""
    canonical_w = HeuristicWeights.from_config()
    
    # Max factors
    max_factors = RiskFactors(
        data_sensitivity=FactorValue(value=1.0, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=1.0, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=1.0, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=1.0, source="test", confidence=1.0),
        cve_risk=FactorValue(value=1.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=1.0, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=1.0, source="test", confidence=1.0)
    )
    res_max = calculate_heuristic_score(max_factors, canonical_w)
    assert math.isclose(res_max.score, 1.0, rel_tol=1e-5)
    
    # Min factors
    min_factors = RiskFactors(
        data_sensitivity=FactorValue(value=0.0, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.0, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.0, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.0, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.0, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.0, source="test", confidence=1.0)
    )
    res_min = calculate_heuristic_score(min_factors, canonical_w)
    assert math.isclose(res_min.score, 0.0, rel_tol=1e-5)


def test_missing_data_policies_under_canonical_weights():
    """Verifies RENORMALIZE and CONSERVATIVE policies under canonical weights."""
    canonical_w = HeuristicWeights.from_config()
    
    # Only crypto_weakness (0.25 weight, value 0.8) and criticality (0.15 weight, value 0.6) are observed.
    partial_factors = RiskFactors(
        data_sensitivity=FactorValue(value=None, source="test", confidence=0.0),
        asset_criticality=FactorValue(value=0.6, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=None, source="test", confidence=0.0),
        crypto_weakness=FactorValue(value=0.8, source="test", confidence=1.0),
        cve_risk=FactorValue(value=None, source="test", confidence=0.0),
        library_centrality=FactorValue(value=None, source="test", confidence=0.0),
        migration_difficulty=FactorValue(value=None, source="test", confidence=0.0)
    )
    
    # RENORMALIZE: Available weight = 0.25 + 0.15 = 0.40
    # Effective crypto = 0.25 / 0.40 = 0.625; effective crit = 0.15 / 0.40 = 0.375
    # Expected score = 0.8 * 0.625 + 0.6 * 0.375 = 0.5 + 0.225 = 0.725
    res_renorm = calculate_heuristic_score(partial_factors, canonical_w, policy=MissingDataPolicy.RENORMALIZE)
    assert math.isclose(res_renorm.score, 0.725, rel_tol=1e-4)
    
    # CONSERVATIVE: Missing factors default to 1.0. Unobserved weight = 1.0 - 0.40 = 0.60
    # Expected score = 0.8 * 0.25 + 0.6 * 0.15 + 1.0 * 0.60 = 0.20 + 0.09 + 0.60 = 0.89
    res_cons = calculate_heuristic_score(partial_factors, canonical_w, policy=MissingDataPolicy.CONSERVATIVE)
    assert math.isclose(res_cons.score, 0.89, rel_tol=1e-4)
