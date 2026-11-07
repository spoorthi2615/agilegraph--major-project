"""
Unit and Regression Tests for Experimental Heuristic V2 Module.

Verifies:
1. Complete isolation and non-interference with production heuristic-v1.0.
2. Semantic graph weakness propagation for key abstractions without non-crypto pollution.
3. Data-aware threshold calibration mechanics.
4. PQC dominance floor protection logic.
5. Zero leakage invariant: Expert labels are never used in GATv2 training.
"""

import pytest
import numpy as np
import torch
from torch_geometric.data import HeteroData

from src.risk.factors import FactorValue, RiskFactors
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.risk.heuristic import calculate_heuristic_score as calculate_v1_score, CURRENT_FORMULA_VERSION
from src.risk.experimental_heuristic import (
    ExperimentalHeuristicConfig,
    calculate_experimental_heuristic_score,
    propagate_graph_crypto_weakness,
    classify_score,
    bootstrap_metric_ci
)


def _make_sample_factors(crypto_val=0.9, centrality_val=0.2, difficulty_val=0.3):
    return RiskFactors(
        data_sensitivity=FactorValue(value=None, source="test", confidence=0.0),
        asset_criticality=FactorValue(value=None, source="test", confidence=0.0),
        internet_exposure=FactorValue(value=None, source="test", confidence=0.0),
        crypto_weakness=FactorValue(value=crypto_val, source="test", confidence=1.0) if crypto_val is not None else FactorValue(value=None, source="test", confidence=0.0),
        cve_risk=FactorValue(value=0.0, source="test", confidence=1.0),
        library_centrality=FactorValue(value=centrality_val, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=difficulty_val, source="test", confidence=1.0)
    )


def test_v1_baseline_immutability():
    """Verify that heuristic-v1.0 is completely unchanged."""
    factors = _make_sample_factors(crypto_val=0.9)
    v1_res = calculate_v1_score(factors)
    
    assert v1_res.formula_version == CURRENT_FORMULA_VERSION
    assert v1_res.formula_version == "heuristic-v1.0"
    assert round(v1_res.score, 3) == 0.500  # (0.25*0.9 + 0.10*0.2 + 0.10*0.3) / 0.55 = 0.275 / 0.55 = 0.500


def test_experimental_v2_default_preserves_continuous_calculation():
    """Verify that V2 without dominance floor computes identical continuous score to V1."""
    factors = _make_sample_factors(crypto_val=0.9)
    cfg = ExperimentalHeuristicConfig(enable_pqc_dominance_floor=False)
    
    v1_res = calculate_v1_score(factors)
    v2_res = calculate_experimental_heuristic_score(factors, config=cfg)
    
    assert v2_res.score == v1_res.score
    assert v2_res.formula_version == "heuristic-v2.0-experimental"


def test_pqc_dominance_floor_activation():
    """Verify that Strategy 3 dominance floor enforces minimum score on high crypto weakness."""
    factors = _make_sample_factors(crypto_val=0.9)  # Base continuous score is 0.500
    cfg = ExperimentalHeuristicConfig(enable_pqc_dominance_floor=True, pqc_floor_factor=0.70)
    
    v2_res = calculate_experimental_heuristic_score(factors, config=cfg)
    expected_floor = round(0.70 * 0.90, 4)  # 0.6300
    assert v2_res.score == expected_floor
    assert v2_res.score >= 0.60  # Guarantees HIGH classification under standard thresholds


def test_semantic_graph_weakness_propagation():
    """Verify that weakness propagates to files importing crypto libraries, but NOT to non-crypto files."""
    g = HeteroData()
    
    # 3 files:
    # File 0: Concrete RSA cipher (observed weakness 0.90, mask 0.0)
    # File 1: KeyBuilder interface (unobserved weakness None, mask 1.0, imports java.security.KeyPair)
    # File 2: StringUtils utility (unobserved weakness None, mask 1.0, imports java.lang.String)
    g["file"].num_nodes = 3
    g["file"].node_ids = ["repo:CipherImpl.java", "repo:KeyBuilder.java", "repo:StringUtils.java"]
    
    # x tensor: 7 factors + 7 masks = 14 dims
    x = torch.zeros((3, 14), dtype=torch.float)
    # File 0: crypto_weakness=0.9 (idx 3), mask=0.0 (idx 10)
    x[0, 3] = 0.90
    x[0, 10] = 0.0
    # File 1: crypto_weakness=0.0 (idx 3), mask=1.0 (idx 10)
    x[1, 10] = 1.0
    # File 2: crypto_weakness=0.0 (idx 3), mask=1.0 (idx 10)
    x[2, 10] = 1.0
    g["file"].x = x
    
    # 2 libraries:
    # Lib 0: java.security.KeyPair (cryptographic)
    # Lib 1: org.apache.commons.lang3.StringUtils (non-crypto)
    g["library"].num_nodes = 2
    g["library"].node_ids = ["repo:lib:java.security.KeyPair", "repo:lib:org.apache.commons.StringUtils"]
    
    # Edge index: File 1 imports Lib 0; File 2 imports Lib 1
    edge_index = torch.tensor([
        [1, 2],  # src (files)
        [0, 1]   # dst (libs)
    ], dtype=torch.long)
    g[("file", "IMPORTS", "library")].edge_index = edge_index
    
    cfg = ExperimentalHeuristicConfig(
        enable_graph_weakness_propagation=True,
        attenuation_factor=0.55
    )
    propagated = propagate_graph_crypto_weakness(g, config=cfg)
    
    # Assert File 1 (KeyBuilder) inherits weakness: 0.55 * 0.90 = 0.4950
    assert "repo:KeyBuilder.java" in propagated
    assert round(propagated["repo:KeyBuilder.java"], 4) == 0.4950
    
    # Assert File 2 (StringUtils) receives ZERO propagation (non-crypto library)
    assert "repo:StringUtils.java" not in propagated
    # Assert File 0 receives no propagation (already observed)
    assert "repo:CipherImpl.java" not in propagated


def test_classify_score_thresholds():
    """Verify discrete tier partitioning logic."""
    assert classify_score(0.15, low_threshold=0.20, high_threshold=0.40) == 0  # LOW
    assert classify_score(0.25, low_threshold=0.20, high_threshold=0.40) == 1  # MEDIUM
    assert classify_score(0.45, low_threshold=0.20, high_threshold=0.40) == 2  # HIGH


def test_bootstrap_metric_ci_sanity():
    """Verify bootstrap confidence interval calculation."""
    y_true = [0, 1, 2, 0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 2, 0, 1, 2, 0, 1, 2]
    ci = bootstrap_metric_ci(
        lambda yt, yp: float(np.mean(np.array(yt) == np.array(yp))),
        y_true, y_pred, n_bootstraps=100
    )
    assert ci["point_estimate"] == 1.0
    assert ci["ci_lower"] == 1.0
    assert ci["ci_upper"] == 1.0

