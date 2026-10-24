import pytest
import numpy as np
from src.risk.weights import HeuristicWeights
from src.risk.factors import RiskFactors, FactorValue
from src.risk.sensitivity_analysis import SensitivityEngine, SinglePerturbationResult


@pytest.fixture
def baseline_weights():
    return HeuristicWeights(
        data_sensitivity=0.20,
        asset_criticality=0.20,
        internet_exposure=0.10,
        crypto_weakness=0.20,
        cve_risk=0.10,
        library_centrality=0.10,
        migration_difficulty=0.10,
    )


@pytest.fixture
def sample_assets():
    # 5 test assets with distinct profiles
    assets = {}
    
    # Asset 1: High crypto weakness, internet facing
    assets["asset_01"] = RiskFactors(
        data_sensitivity=FactorValue(value=0.8, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.9, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=1.0, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=1.0, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.5, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.4, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.7, source="test", confidence=1.0),
    )

    # Asset 2: Pure classical weak crypto, low exposure
    assets["asset_02"] = RiskFactors(
        data_sensitivity=FactorValue(value=0.2, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.3, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.2, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.9, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.1, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.2, source="test", confidence=1.0),
    )

    # Asset 3: High centrality library, low crypto weakness
    assets["asset_03"] = RiskFactors(
        data_sensitivity=FactorValue(value=0.5, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.5, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.5, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.1, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.2, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.9, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.8, source="test", confidence=1.0),
    )

    # Asset 4: Balanced moderate risk
    assets["asset_04"] = RiskFactors(
        data_sensitivity=FactorValue(value=0.5, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.5, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.5, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.5, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.5, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.5, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.5, source="test", confidence=1.0),
    )

    # Asset 5: Low risk overall
    assets["asset_05"] = RiskFactors(
        data_sensitivity=FactorValue(value=0.1, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.1, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.1, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=0.1, source="test", confidence=1.0),
        cve_risk=FactorValue(value=0.1, source="test", confidence=1.0),
        library_centrality=FactorValue(value=0.1, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.1, source="test", confidence=1.0),
    )

    return assets


def test_perturb_single_factor_sum_normalization(baseline_weights):
    # Perturb crypto_weakness up by +10%
    perturbed = SensitivityEngine.perturb_single_factor(baseline_weights, "crypto_weakness", 0.10)
    assert perturbed.crypto_weakness > 0.20
    # Check exact sum constraint
    total = sum(perturbed.model_dump().values())
    assert abs(total - 1.0) < 1e-5


def test_perturb_single_factor_down_20_percent(baseline_weights):
    # Perturb crypto_weakness down by -20%
    perturbed = SensitivityEngine.perturb_single_factor(baseline_weights, "crypto_weakness", -0.20)
    assert perturbed.crypto_weakness < 0.20
    # Check exact sum constraint
    total = sum(perturbed.model_dump().values())
    assert abs(total - 1.0) < 1e-5


def test_generate_all_28_perturbations(baseline_weights):
    # 7 factors * 4 deltas (-20%, -10%, +10%, +20%) = 28 runs
    perturbations = SensitivityEngine.generate_perturbations(baseline_weights)
    assert len(perturbations) == 28

    # Verify every weight set sums to 1.0
    for p in perturbations:
        total = sum(p.weights.model_dump().values())
        assert abs(total - 1.0) < 1e-5


def test_run_sensitivity_study_metrics(baseline_weights, sample_assets):
    report = SensitivityEngine.run_sensitivity_study(
        baseline=baseline_weights,
        asset_factors=sample_assets,
        deltas=[-0.20, -0.10, 0.10, 0.20]
    )

    assert report.evaluated_assets_count == 5
    assert len(report.results) == 28
    assert "ranking_stable" in report.stability_summary
    assert report.stability_summary["total_perturbations_tested"] == 28
    assert report.stability_summary["min_spearman_rho"] >= 0.80

    first_result = report.results[0]
    assert isinstance(first_result, SinglePerturbationResult)
    assert first_result.spearman_rank_correlation is not None
    assert first_result.kendall_tau is not None
    assert len(first_result.asset_shifts) == 5
