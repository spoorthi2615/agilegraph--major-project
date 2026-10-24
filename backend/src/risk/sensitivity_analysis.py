import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from src.risk.weights import HeuristicWeights
from src.risk.factors import RiskFactors
from src.risk.score import RiskScoreResult, MissingDataPolicy
from src.risk.heuristic import calculate_heuristic_score, rank_assets


class PerturbedWeightSet(BaseModel):
    factor_perturbed: str
    delta_percent: float
    weights: HeuristicWeights


class AssetScoreShift(BaseModel):
    asset_id: str
    baseline_score: Optional[float]
    perturbed_score: Optional[float]
    score_difference: Optional[float]
    baseline_rank: int
    perturbed_rank: int
    rank_difference: int


class SinglePerturbationResult(BaseModel):
    factor_perturbed: str
    delta_percent: float
    weights: Dict[str, float]
    mean_absolute_score_change: float
    max_absolute_score_change: float
    spearman_rank_correlation: Optional[float]
    kendall_tau: Optional[float]
    top_10_overlap_ratio: float
    top_20_overlap_ratio: float
    asset_shifts: List[AssetScoreShift]


class SensitivityReport(BaseModel):
    baseline_weights: Dict[str, float]
    evaluated_assets_count: int
    perturbation_levels: List[float]
    results: List[SinglePerturbationResult]
    stability_summary: Dict[str, Any]


class SensitivityEngine:
    """
    Automated one-at-a-time (OAT) sensitivity analysis engine for AgileGraph's 7 heuristic weights.
    Tests perturbations of ±10% and ±20% with proportional simplex renormalization.
    Computes score variance, ranking stability (Spearman rho, Kendall tau), and top-K migration stability.
    """

    FACTORS = [
        "data_sensitivity",
        "asset_criticality",
        "internet_exposure",
        "crypto_weakness",
        "cve_risk",
        "library_centrality",
        "migration_difficulty",
    ]

    @staticmethod
    def perturb_single_factor(
        baseline: HeuristicWeights,
        target_factor: str,
        delta_percent: float
    ) -> HeuristicWeights:
        """
        Perturbs a target factor by delta_percent (e.g. +0.10, -0.10, +0.20, -0.20).
        Renormalizes all other weights proportionally so sum(w) == 1.0.
        """
        raw = baseline.model_dump()
        if target_factor not in raw:
            raise ValueError(f"Unknown factor {target_factor}")

        current_val = raw[target_factor]
        # Multiplicative perturbation: new = val * (1 + delta)
        new_val = max(0.0, min(1.0, current_val * (1.0 + delta_percent)))
        diff = new_val - current_val

        # Remaining weight available in other factors
        other_keys = [k for k in raw.keys() if k != target_factor]
        sum_others = sum(raw[k] for k in other_keys)

        new_dict = {target_factor: new_val}

        if sum_others > 0:
            for k in other_keys:
                # Adjust remaining proportionally
                fraction = raw[k] / sum_others
                adjusted = max(0.0, raw[k] - (diff * fraction))
                new_dict[k] = adjusted
        else:
            # If others sum to 0, distribute equally
            for k in other_keys:
                new_dict[k] = max(0.0, -diff / len(other_keys))

        # Mathematical normalization to ensure strict sum == 1.0
        total = sum(new_dict.values())
        for k in new_dict:
            new_dict[k] = new_dict[k] / total

        return HeuristicWeights(**new_dict)

    @staticmethod
    def generate_perturbations(
        baseline: HeuristicWeights,
        deltas: Optional[List[float]] = None
    ) -> List[PerturbedWeightSet]:
        """
        Generates weight sets for all 7 factors across ±10% and ±20% perturbations.
        For 7 factors and 4 deltas (-0.20, -0.10, +0.10, +0.20), generates 28 perturbed configurations.
        """
        perturbation_deltas = deltas or [-0.20, -0.10, 0.10, 0.20]
        results = []

        for factor in SensitivityEngine.FACTORS:
            for delta in perturbation_deltas:
                p_weights = SensitivityEngine.perturb_single_factor(baseline, factor, delta)
                results.append(PerturbedWeightSet(
                    factor_perturbed=factor,
                    delta_percent=delta,
                    weights=p_weights
                ))

        return results

    @staticmethod
    def run_sensitivity_study(
        baseline: HeuristicWeights,
        asset_factors: Dict[str, RiskFactors],
        deltas: Optional[List[float]] = None,
        policy: MissingDataPolicy = MissingDataPolicy.RENORMALIZE
    ) -> SensitivityReport:
        """
        Runs sensitivity analysis across all provided assets.
        Scores each asset under baseline and perturbed weights, ranking and calculating stability metrics.
        """
        perturbation_deltas = deltas or [-0.20, -0.10, 0.10, 0.20]
        all_perturbations = SensitivityEngine.generate_perturbations(baseline, perturbation_deltas)

        # 1. Compute baseline scores and rankings
        baseline_scores = {}
        for asset_id, factors in asset_factors.items():
            res = calculate_heuristic_score(factors, baseline, policy=policy)
            baseline_scores[asset_id] = res

        baseline_rankings = rank_assets(baseline_scores) # List of (rank, asset_id, score)
        baseline_rank_map = {asset_id: rank for rank, asset_id, _ in baseline_rankings}
        baseline_order = [asset_id for _, asset_id, _ in baseline_rankings]

        perturbation_results = []
        all_spearman = []

        for p in all_perturbations:
            # Score under perturbed weights
            p_scores = {}
            for asset_id, factors in asset_factors.items():
                p_scores[asset_id] = calculate_heuristic_score(factors, p.weights, policy=policy)

            p_rankings = rank_assets(p_scores)
            p_rank_map = {asset_id: rank for rank, asset_id, _ in p_rankings}

            # Asset level shifts
            asset_shifts = []
            abs_score_diffs = []
            baseline_ranks_list = []
            perturbed_ranks_list = []

            for asset_id in baseline_order:
                b_score = baseline_scores[asset_id].score
                pt_score = p_scores[asset_id].score
                b_rank = baseline_rank_map[asset_id]
                pt_rank = p_rank_map[asset_id]

                diff = abs(pt_score - b_score) if (pt_score is not None and b_score is not None) else None
                if diff is not None:
                    abs_score_diffs.append(diff)

                baseline_ranks_list.append(b_rank)
                perturbed_ranks_list.append(pt_rank)

                asset_shifts.append(AssetScoreShift(
                    asset_id=asset_id,
                    baseline_score=round(b_score, 4) if b_score is not None else None,
                    perturbed_score=round(pt_score, 4) if pt_score is not None else None,
                    score_difference=round(diff, 4) if diff is not None else None,
                    baseline_rank=b_rank,
                    perturbed_rank=pt_rank,
                    rank_difference=pt_rank - b_rank
                ))

            # Rank correlations
            import scipy.stats as stats
            if len(baseline_ranks_list) > 1:
                rho, _ = stats.spearmanr(baseline_ranks_list, perturbed_ranks_list)
                tau, _ = stats.kendalltau(baseline_ranks_list, perturbed_ranks_list)
                rho_val = float(rho) if not np.isnan(rho) else 1.0
                tau_val = float(tau) if not np.isnan(tau) else 1.0
            else:
                rho_val = 1.0
                tau_val = 1.0

            all_spearman.append(rho_val)

            # Top-K overlap
            top10_base = set(baseline_order[:10])
            top10_pert = set([aid for _, aid, _ in p_rankings[:10]])
            top10_overlap = len(top10_base.intersection(top10_pert)) / min(10, max(1, len(top10_base)))

            top20_base = set(baseline_order[:20])
            top20_pert = set([aid for _, aid, _ in p_rankings[:20]])
            top20_overlap = len(top20_base.intersection(top20_pert)) / min(20, max(1, len(top20_base)))

            perturbation_results.append(SinglePerturbationResult(
                factor_perturbed=p.factor_perturbed,
                delta_percent=p.delta_percent,
                weights={k: round(v, 4) for k, v in p.weights.model_dump().items()},
                mean_absolute_score_change=round(float(np.mean(abs_score_diffs)), 4) if abs_score_diffs else 0.0,
                max_absolute_score_change=round(float(np.max(abs_score_diffs)), 4) if abs_score_diffs else 0.0,
                spearman_rank_correlation=round(rho_val, 4),
                kendall_tau=round(tau_val, 4),
                top_10_overlap_ratio=round(top10_overlap, 4),
                top_20_overlap_ratio=round(top20_overlap, 4),
                asset_shifts=asset_shifts
            ))

        stability_summary = {
            "total_perturbations_tested": len(all_perturbations),
            "min_spearman_rho": round(float(np.min(all_spearman)), 4) if all_spearman else 1.0,
            "mean_spearman_rho": round(float(np.mean(all_spearman)), 4) if all_spearman else 1.0,
            "ranking_stable": bool(np.min(all_spearman) >= 0.90) if all_spearman else True
        }

        return SensitivityReport(
            baseline_weights=baseline.model_dump(),
            evaluated_assets_count=len(asset_factors),
            perturbation_levels=perturbation_deltas,
            results=perturbation_results,
            stability_summary=stability_summary
        )
