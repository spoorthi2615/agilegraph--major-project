import pytest
from src.risk.weights import HeuristicWeights, perturb_weights

def test_weights_sum_to_one():
    weights = HeuristicWeights(
        data_sensitivity=0.2,
        asset_criticality=0.2,
        internet_exposure=0.1,
        crypto_weakness=0.2,
        cve_risk=0.1,
        library_centrality=0.1,
        migration_difficulty=0.1
    )
    assert weights is not None

def test_weights_invalid_sum():
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        HeuristicWeights(
            data_sensitivity=0.2,
            asset_criticality=0.2,
            internet_exposure=0.1,
            crypto_weakness=0.2,
            cve_risk=0.1,
            library_centrality=0.1,
            migration_difficulty=0.2 # Sum is 1.1
        )

def test_weights_out_of_bounds():
    with pytest.raises(ValueError):
        HeuristicWeights(
            data_sensitivity=1.2, # Invalid
            asset_criticality=0.0,
            internet_exposure=0.0,
            crypto_weakness=0.0,
            cve_risk=0.0,
            library_centrality=0.0,
            migration_difficulty=-0.2
        )

def test_perturb_weights():
    weights = HeuristicWeights(
        data_sensitivity=0.2,
        asset_criticality=0.2,
        internet_exposure=0.1,
        crypto_weakness=0.2,
        cve_risk=0.1,
        library_centrality=0.1,
        migration_difficulty=0.1
    )
    perturbed = perturb_weights(weights, perturbation=0.10)
    assert perturbed.crypto_weakness > 0.2
    # Ensure they still sum to 1
    total = sum(perturbed.model_dump().values())
    assert abs(total - 1.0) < 1e-5
