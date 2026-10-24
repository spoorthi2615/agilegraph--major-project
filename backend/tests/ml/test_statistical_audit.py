import pytest
import numpy as np
from run_benchmark_step3 import compute_baseline_statistics


def test_statistics_constant_rankings_zero_variance():
    # When all scores in an array are identical, correlation is mathematically undefined
    h = [0.5, 0.5, 0.5, 0.5]
    r = [0.2, 0.4, 0.6, 0.8]
    res = compute_baseline_statistics(h, r)

    assert res["status"] == "UNDEFINED"
    assert res["spearman_rho"] is None
    assert res["kendall_tau"] is None
    assert "Zero variance" in res["reason"]


def test_statistics_legitimate_zero_correlation():
    # Both vectors have variance, but monotonic rank association is 0.0
    # e.g. symmetrically inverted ranks
    h = [1.0, 2.0, 3.0, 4.0, 5.0]
    r = [2.0, 4.0, 1.0, 5.0, 3.0]  # Let's check a known orthogonal or uncorrelated ranking
    # h ranks: 1, 2, 3, 4, 5
    # Let's construct exact zero correlation:
    # ranks: [1, 2, 4, 5], [2, 4, 1, 3] -> sum of (x-xbar)(y-ybar) = 0
    # x = [1, 2, 3, 4], xbar = 2.5, (x-xbar) = [-1.5, -0.5, 0.5, 1.5]
    # y = [2, 4, 1, 3], ybar = 2.5, (y-ybar) = [-0.5, 1.5, -1.5, 0.5]
    # prod = 0.75 - 0.75 - 0.75 + 0.75 = 0.0!
    h_zero = [1.0, 2.0, 3.0, 4.0]
    r_zero = [2.0, 4.0, 1.0, 3.0]
    res_zero = compute_baseline_statistics(h_zero, r_zero)
    assert res_zero["status"] == "DEFINED"
    assert res_zero["spearman_rho"] is not None
    assert abs(res_zero["spearman_rho"]) < 1e-6


def test_statistics_small_sample_size():
    # N = 1 is insufficient for correlation
    res_one = compute_baseline_statistics([0.5], [0.3])
    assert res_one["status"] == "UNDEFINED"
    assert res_one["spearman_rho"] is None
    assert "N < 2 is insufficient" in res_one["reason"]

    # N = 2 is computable mathematically for Spearman, but permutation test is degenerate
    res_two = compute_baseline_statistics([0.1, 0.9], [0.2, 0.8])
    assert res_two["status"] == "DEFINED"
    assert res_two["comparable_assets_count"] == 2
    assert res_two["spearman_rho"] == 1.0

    # N = 3 is computable and has valid bootstrap/permutation
    res_three = compute_baseline_statistics([0.1, 0.5, 0.9], [0.2, 0.6, 0.8])
    assert res_three["status"] == "DEFINED"
    assert res_three["comparable_assets_count"] == 3
    assert res_three["spearman_rho"] == 1.0


def test_statistics_permutation_finite_sample_correction():
    # With N=20, 2^20 > 1,000,000 possible sign combinations.
    # When diffs completely separate, empirical k=0, so finite sample correction yields exactly (0+1)/(10000+1) ~ 0.0001
    h = list(np.linspace(0.1, 0.4, 20))
    r = list(np.linspace(0.8, 1.0, 20))
    res = compute_baseline_statistics(h, r)

    details = res["permutation_test_details"]
    assert details["num_permutations"] == 10000
    assert details["finite_sample_corrected_pvalue"] > 0.0
    assert details["finite_sample_corrected_pvalue"] <= 0.0001


def test_statistics_tied_rankings_handled():
    # Handled via fractional/mid-rank assignment in scipy
    h = [0.2, 0.2, 0.8, 0.8]
    r = [0.1, 0.3, 0.7, 0.9]
    res = compute_baseline_statistics(h, r)

    assert res["status"] == "DEFINED"
    assert res["spearman_rho"] is not None
    assert 0.8 <= res["spearman_rho"] <= 1.0
