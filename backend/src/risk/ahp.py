import numpy as np
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


# Standard 7 factors used in AgileGraph Heuristic Risk Engine
HEURISTIC_FACTORS = [
    "data_sensitivity",
    "asset_criticality",
    "internet_exposure",
    "crypto_weakness",
    "cve_risk",
    "library_centrality",
    "migration_difficulty",
]

# Random Consistency Index (RI) table for matrix sizes n=1..10 per Saaty (1980)
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}

# Saaty Fundamental Scale mappings
SAATY_SCALE_DESCRIPTIONS = {
    1: "Equal Importance",
    3: "Moderate Importance of one factor over another",
    5: "Strong Importance of one factor over another",
    7: "Very Strong or Demonstrated Importance",
    9: "Extreme Importance",
    2: "Intermediate value between 1 and 3",
    4: "Intermediate value between 3 and 5",
    6: "Intermediate value between 5 and 7",
    8: "Intermediate value between 7 and 9",
}


class PairwiseComparison(BaseModel):
    factor_a: str
    factor_b: str
    relative_importance: float = Field(
        ...,
        description="Saaty score: >1 means factor_a is more important, 1 means equal, <1 means factor_b is more important (1/x)."
    )
    rationale: Optional[str] = None


class AHPSurveyResponse(BaseModel):
    reviewer_id: str
    comparisons: List[PairwiseComparison]
    submission_status: str = "SUBMITTED"
    timestamp: Optional[str] = None


class AHPResult(BaseModel):
    factors: List[str]
    weights: Dict[str, float]
    lambda_max: float
    consistency_index: float
    consistency_ratio: float
    is_consistent: bool
    status: str
    message: Optional[str] = None


class AHPEngine:
    """
    Analytic Hierarchy Process (AHP-lite) engine for eliciting, validating,
    and deriving consensus weights across the 7 post-quantum crypto-agility risk factors.
    """

    @staticmethod
    def generate_questionnaire_template(factors: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generates all pairwise comparison prompts (n*(n-1)/2 items) for experts.
        For 7 factors, this generates exactly 21 comparisons.
        """
        f_list = factors or HEURISTIC_FACTORS
        questions = []
        n = len(f_list)
        q_id = 1
        for i in range(n):
            for j in range(i + 1, n):
                fa = f_list[i]
                fb = f_list[j]
                questions.append({
                    "question_id": f"Q{q_id:02d}",
                    "factor_a": fa,
                    "factor_b": fb,
                    "prompt": f"Compare relative importance for PQC migration prioritization: '{fa}' vs '{fb}'",
                    "valid_values": [1/9, 1/7, 1/5, 1/3, 1, 3, 5, 7, 9],
                    "instructions": "Assign 1 (equal), 3 (moderate A>B), 5 (strong A>B), 7 (very strong A>B), 9 (extreme A>B), or reciprocal 1/x if B>A."
                })
                q_id += 1
        return questions

    @staticmethod
    def build_matrix_from_comparisons(
        comparisons: List[PairwiseComparison],
        factors: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Constructs a reciprocal pairwise comparison matrix A where a_ij = 1 / a_ji and a_ii = 1.
        """
        f_list = factors or HEURISTIC_FACTORS
        n = len(f_list)
        f_idx = {name: idx for idx, name in enumerate(f_list)}
        
        matrix = np.ones((n, n), dtype=float)

        for comp in comparisons:
            if comp.factor_a not in f_idx or comp.factor_b not in f_idx:
                continue
            i = f_idx[comp.factor_a]
            j = f_idx[comp.factor_b]
            val = float(comp.relative_importance)
            if val <= 0:
                raise ValueError(f"Pairwise comparison value must be strictly positive, got {val}")
            
            matrix[i, j] = val
            matrix[j, i] = 1.0 / val

        return matrix

    @staticmethod
    def derive_weights(
        matrix: np.ndarray,
        factors: Optional[List[str]] = None
    ) -> AHPResult:
        """
        Derives normalized priority weights using the principal right eigenvector method,
        calculates lambda_max, Consistency Index (CI), and Consistency Ratio (CR).
        Threshold for consistency is CR < 0.10 (Saaty, 1980).
        """
        f_list = factors or HEURISTIC_FACTORS
        n = len(f_list)

        if matrix.shape != (n, n):
            raise ValueError(f"Matrix shape {matrix.shape} does not match factor count {n}")

        # Compute eigenvalues and eigenvectors
        eigvals, eigvecs = np.linalg.eig(matrix)
        
        # Principal eigenvalue is maximum real eigenvalue
        max_idx = np.argmax(np.real(eigvals))
        lambda_max = float(np.real(eigvals[max_idx]))
        
        # Principal eigenvector (normalized to sum to 1.0)
        principal_vec = np.real(eigvecs[:, max_idx])
        # If vector is negative, flip sign
        if np.sum(principal_vec) < 0:
            principal_vec = -principal_vec
        
        weights_arr = principal_vec / np.sum(principal_vec)
        # Ensure all strictly non-negative
        weights_arr = np.maximum(weights_arr, 0.0)
        weights_arr = weights_arr / np.sum(weights_arr)

        # Consistency metrics
        if n <= 2:
            ci = 0.0
            cr = 0.0
        else:
            ci = (lambda_max - n) / (n - 1)
            ri = RANDOM_INDEX.get(n, 1.49)
            cr = ci / ri if ri > 0 else 0.0

        is_consistent = bool(cr < 0.10)
        weights_dict = {f_list[i]: round(float(weights_arr[i]), 5) for i in range(n)}

        # Re-verify sum is exactly 1.0 after rounding adjustment
        diff = 1.0 - sum(weights_dict.values())
        if abs(diff) > 0:
            first_k = f_list[0]
            weights_dict[first_k] = round(weights_dict[first_k] + diff, 5)

        return AHPResult(
            factors=f_list,
            weights=weights_dict,
            lambda_max=round(lambda_max, 4),
            consistency_index=round(ci, 4),
            consistency_ratio=round(cr, 4),
            is_consistent=is_consistent,
            status="COMPUTED",
            message="Consistent" if is_consistent else f"Inconsistent (CR = {cr:.4f} >= 0.10). Expert revision recommended."
        )

    @staticmethod
    def aggregate_group_weights(
        expert_matrices: List[np.ndarray],
        factors: Optional[List[str]] = None
    ) -> AHPResult:
        """
        Aggregates multiple expert comparison matrices using geometric mean aggregation (AHP-WGMM),
        which preserves reciprocity in group decision-making.
        """
        if not expert_matrices:
            return AHPResult(
                factors=factors or HEURISTIC_FACTORS,
                weights={f: 1.0 / len(factors or HEURISTIC_FACTORS) for f in (factors or HEURISTIC_FACTORS)},
                lambda_max=0.0,
                consistency_index=0.0,
                consistency_ratio=0.0,
                is_consistent=False,
                status="NO_MATRICES_PROVIDED",
                message="No comparison matrices provided."
            )

        f_list = factors or HEURISTIC_FACTORS
        n = len(f_list)
        stacked = np.stack(expert_matrices, axis=0) # (num_experts, n, n)
        
        # Geometric mean across experts
        # a_ij^group = (prod_k a_ij^(k))^(1/K)
        geom_matrix = np.exp(np.mean(np.log(stacked), axis=0))

        return AHPEngine.derive_weights(geom_matrix, factors=f_list)
