import pytest
from src.risk.heuristic import calculate_heuristic_score, rank_assets
from src.risk.factors import RiskFactors, FactorValue
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy

def get_test_weights():
    return HeuristicWeights(
        data_sensitivity=0.2,
        asset_criticality=0.2,
        internet_exposure=0.1,
        crypto_weakness=0.2,
        cve_risk=0.1,
        library_centrality=0.1,
        migration_difficulty=0.1
    )

def get_complete_factors():
    return RiskFactors(
        data_sensitivity=FactorValue(value=1.0, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.5, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=1.0, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.0, source="test", confidence=1.0),
        cve_risk=FactorValue(value=1.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.5, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.2, source="test", confidence=1.0)
    )

def test_heuristic_score_reproducibility():
    w = get_test_weights()
    f = get_complete_factors()
    
    res1 = calculate_heuristic_score(f, w)
    res2 = calculate_heuristic_score(f, w)
    
    assert res1.score == res2.score
    assert res1.score == (1.0*0.2 + 0.5*0.2 + 1.0*0.1 + 0.0*0.2 + 1.0*0.1 + 0.5*0.1 + 0.2*0.1)

def test_missing_data_strict_policy():
    w = get_test_weights()
    f = get_complete_factors()
    f.internet_exposure = FactorValue(value=None, source="none", confidence=0.0)
    
    with pytest.raises(ValueError, match="STRICT policy violation"):
        calculate_heuristic_score(f, w, policy=MissingDataPolicy.STRICT)

def test_missing_data_renormalize_policy():
    w = get_test_weights()
    f = get_complete_factors()
    f.internet_exposure = FactorValue(value=None, source="none", confidence=0.0) # weight 0.1
    
    res = calculate_heuristic_score(f, w, policy=MissingDataPolicy.RENORMALIZE)
    assert "internet_exposure" in res.missing_factors
    assert res.score > 0.0 # It should still compute a score
    assert "Renormalized" in res.assumptions[-1]
    
    # Total valid weight is 0.9. 
    # data_sensitivity val=1.0, w=0.2 -> effective=0.2/0.9
    expected_ds_contrib = 1.0 * (0.2 / 0.9)
    assert abs(res.weighted_contributions["data_sensitivity"].contribution - expected_ds_contrib) < 1e-5

def test_factor_out_of_bounds():
    w = get_test_weights()
    f = get_complete_factors()
    f.data_sensitivity = FactorValue(value=1.5, source="test", confidence=1.0)
    
    with pytest.raises(ValueError, match="Factor data_sensitivity out of bounds"):
        calculate_heuristic_score(f, w)

def test_synthetic_ranking_fixture():
    """
    SYNTHETIC TEST DATA
    NOT REAL SECURITY ASSESSMENTS
    """
    w = get_test_weights()
    
    fA = get_complete_factors() # Score: 0.57
    fB = get_complete_factors()
    fB.crypto_weakness = FactorValue(value=1.0, source="test", confidence=1.0) # Higher risk
    fC = get_complete_factors()
    fC.data_sensitivity = FactorValue(value=0.0, source="test", confidence=1.0) # Lower risk
    
    resA = calculate_heuristic_score(fA, w)
    resB = calculate_heuristic_score(fB, w)
    resC = calculate_heuristic_score(fC, w)
    
    assets = {
        "Asset A": resA,
        "Asset B": resB,
        "Asset C": resC
    }
    
    ranking = rank_assets(assets)
    # Asset B should be first (highest risk)
    assert ranking[0][1] == "Asset B"
    assert ranking[1][1] == "Asset A"
    assert ranking[2][1] == "Asset C"
    
    # Check deterministic tie break by name
    assets["Asset B2"] = resB
    ranking_tied = rank_assets(assets)
    # B and B2 have same score, 'Asset B' < 'Asset B2'
    assert ranking_tied[0][1] == "Asset B"
    assert ranking_tied[1][1] == "Asset B2"
