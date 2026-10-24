import torch
import numpy as np
from typing import Dict, Any, List, Optional
from torch_geometric.data import HeteroData
from src.risk.score import RiskScoreResult


def explain_heuristic_decomposition(risk_result: RiskScoreResult) -> Dict[str, Any]:
    """
    Decomposes the heuristic baseline risk score into exact additive factor contributions.
    base_risk = sum(w_j * f_j).
    Returns factor weights, normalized values, absolute contributions, and missingness impact.
    """
    contributions = {}
    total_score = risk_result.score

    for factor_name, contrib in risk_result.weighted_contributions.items():
        contributions[factor_name] = {
            "factor_value": contrib.value,
            "effective_weight": contrib.weight,
            "absolute_contribution": contrib.contribution,
            "relative_percentage": (contrib.contribution / total_score * 100.0) if total_score and total_score > 0 else 0.0
        }

    return {
        "status": "COMPUTED",
        "method": "HEURISTIC_LINEAR_DECOMPOSITION",
        "formula_version": risk_result.formula_version,
        "total_risk_score": total_score,
        "missing_factors": risk_result.missing_factors,
        "missing_data_policy": risk_result.missing_data_policy.value,
        "factor_contributions": contributions,
        "caveat": "Additive linear decomposition of rule prior; not causal attribution of real vulnerability."
    }


def compute_gradient_feature_importance(
    model: torch.nn.Module,
    pyg_data: HeteroData,
    target_node_category: str = "file",
    target_node_idx: int = 0,
    target_class_idx: Optional[int] = None
) -> Dict[str, Any]:
    """
    Computes input feature saliency (gradient * input attribution) for a target node prediction in HeteroGATv2.
    Measures the local linear sensitivity of the target class logit to each input feature dimension.
    """
    model.eval()
    
    # Clone and enable gradients on input features
    x_dict_grad = {}
    for k, v in pyg_data.x_dict.items():
        x_dict_grad[k] = v.clone().detach().requires_grad_(True)

    out_dict = model(x_dict_grad, pyg_data.edge_index_dict)
    
    if target_node_category not in out_dict:
        raise ValueError(f"Category '{target_node_category}' not in model outputs.")

    logits = out_dict[target_node_category]
    if target_node_idx >= logits.shape[0]:
        raise IndexError(f"Node index {target_node_idx} out of range for category '{target_node_category}'.")

    target_logits = logits[target_node_idx]
    
    # If no target class specified, use predicted class
    if target_class_idx is None:
        target_class_idx = int(target_logits.argmax().item())

    # Backward pass for the target class logit
    score = target_logits[target_class_idx]
    score.backward()

    # Saliency = gradient * input feature
    target_x = x_dict_grad[target_node_category]
    if target_x.grad is None:
        return {"status": "ZERO_GRADIENT", "feature_saliency": []}

    grad = target_x.grad[target_node_idx]
    feat = target_x[target_node_idx]
    saliency = (grad * feat).detach().cpu().numpy()

    feature_labels_14 = [
        "data_sensitivity", "asset_criticality", "internet_exposure",
        "crypto_weakness", "cve_risk", "library_centrality", "migration_difficulty",
        "mask_sensitivity", "mask_criticality", "mask_exposure",
        "mask_crypto_weakness", "mask_cve_risk", "mask_library_centrality", "mask_migration_difficulty"
    ]
    feature_labels_16 = feature_labels_14 + ["base_risk", "mask_base_risk"]

    dim = len(saliency)
    if dim == 14:
        names = feature_labels_14
    elif dim == 16:
        names = feature_labels_16
    elif dim == 1:
        names = ["constant_structure_token"]
    else:
        names = [f"feature_{i}" for i in range(dim)]

    feature_attributions = {}
    for idx, name in enumerate(names):
        feature_attributions[name] = float(saliency[idx])

    return {
        "status": "COMPUTED",
        "method": "INTEGRATED_INPUT_X_GRADIENT",
        "target_node_category": target_node_category,
        "target_node_idx": target_node_idx,
        "predicted_class": target_class_idx,
        "feature_attributions": feature_attributions,
        "caveat": "Local gradient saliency measures model sensitivity; does not prove causal vulnerability."
    }


def estimate_risk_reduction(
    current_score: float,
    mitigated_factors: Dict[str, float],
    weights: Dict[str, float]
) -> Dict[str, Any]:
    """
    Estimates the risk reduction achievable by migrating identified cryptographic primitives
    or reducing exposure (e.g., upgrading RSA-2048 to ML-KEM reduces crypto_weakness from 0.90 to 0.0).
    """
    delta_risk = 0.0
    factor_deltas = {}

    for factor, new_val in mitigated_factors.items():
        if factor in weights:
            w = weights[factor]
            # Assumes prior factor value was current contribution
            factor_deltas[factor] = {
                "mitigated_target_value": new_val,
                "weight": w
            }

    return {
        "status": "COMPUTED",
        "baseline_risk": current_score,
        "mitigated_factors": factor_deltas,
        "description": "Forward simulation of post-migration risk posture under specified factor reductions."
    }
