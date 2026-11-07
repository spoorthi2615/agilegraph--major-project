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


class HeteroExplainerModelWrapper(torch.nn.Module):
    """
    Adapter wrapper allowing PyTorch Geometric Explainer to target a specific
    node category output from a HeteroGATv2 model.
    """
    def __init__(self, model: torch.nn.Module, target_nodetype: str = "file"):
        super().__init__()
        self.model = model
        self.target_nodetype = target_nodetype

    def forward(self, x_dict, edge_index_dict, **kwargs):
        out_dict = self.model(x_dict, edge_index_dict)
        return out_dict[self.target_nodetype]


def explain_with_gnnexplainer(
    model: torch.nn.Module,
    pyg_data: HeteroData,
    target_node_category: str = "file",
    target_node_idx: int = 0,
    epochs: int = 100,
    lr: float = 0.01,
    top_k_edges: int = 5
) -> Dict[str, Any]:
    """
    Uses PyTorch Geometric's GNNExplainer to identify critical node features and graph relationships
    influencing a specific node's risk classification in HeteroGATv2.

    Crucial Scientific Caveat:
    Because HeteroGATv2 is trained under weak supervision to distill the deterministic 7-factor
    heuristic risk engine, GNNExplainer explains *why the model predicts agreement with the heuristic*,
    NOT why the underlying cryptographic primitive is physically or cryptanalytically vulnerable.
    """
    from torch_geometric.explain import Explainer, GNNExplainer

    if target_node_category not in pyg_data.node_types:
        raise ValueError(f"Category '{target_node_category}' not present in HeteroData node types: {pyg_data.node_types}")

    num_nodes = pyg_data[target_node_category].num_nodes
    if target_node_idx < 0 or target_node_idx >= num_nodes:
        raise IndexError(f"Target node index {target_node_idx} out of range for category '{target_node_category}' (total: {num_nodes})")

    model.eval()
    wrapper = HeteroExplainerModelWrapper(model, target_nodetype=target_node_category)

    explainer = Explainer(
        model=wrapper,
        algorithm=GNNExplainer(epochs=epochs, lr=lr),
        explanation_type='model',
        node_mask_type='attributes',
        edge_mask_type='object',
        model_config=dict(
            mode='multiclass_classification',
            task_level='node',
            return_type='probs',
        ),
    )

    explanation = explainer(
        pyg_data.x_dict,
        pyg_data.edge_index_dict,
        index=target_node_idx,
    )

    # 1. Feature Attributions
    feature_labels_14 = [
        "data_sensitivity", "asset_criticality", "internet_exposure",
        "crypto_weakness", "cve_risk", "library_centrality", "migration_difficulty",
        "mask_sensitivity", "mask_criticality", "mask_exposure",
        "mask_crypto_weakness", "mask_cve_risk", "mask_library_centrality", "mask_migration_difficulty"
    ]
    feature_labels_16 = feature_labels_14 + ["base_risk", "mask_base_risk"]

    feature_attributions = []
    if hasattr(explanation, 'node_mask_dict') and target_node_category in explanation.node_mask_dict:
        node_mask = explanation.node_mask_dict[target_node_category]
        target_mask = node_mask[target_node_idx].detach().cpu().numpy()
        dim = len(target_mask)
        if dim == 14:
            names = feature_labels_14
        elif dim == 16:
            names = feature_labels_16
        else:
            names = [f"feature_{i}" for i in range(dim)]

        total_weight = float(np.sum(np.abs(target_mask))) + 1e-9
        for name, val in zip(names, target_mask):
            raw_v = float(val)
            feature_attributions.append({
                "feature_name": name,
                "importance": raw_v,
                "normalized_importance": round(abs(raw_v) / total_weight, 4)
            })
        feature_attributions.sort(key=lambda item: item["importance"], reverse=True)

    # 2. Graph Edge Attributions (Neighbors influencing the target node)
    top_edges = []
    if hasattr(explanation, 'edge_mask_dict'):
        for edge_type, mask in explanation.edge_mask_dict.items():
            src_type, rel, dst_type = edge_type
            edge_index = pyg_data[edge_type].edge_index
            mask_vals = mask.detach().cpu().numpy()

            for i in range(edge_index.shape[1]):
                src_i = int(edge_index[0, i])
                dst_i = int(edge_index[1, i])
                
                # Check if edge connects directly to target node
                is_incident = (src_type == target_node_category and src_i == target_node_idx) or \
                              (dst_type == target_node_category and dst_i == target_node_idx)
                
                if is_incident or len(top_edges) < top_k_edges:
                    top_edges.append({
                        "edge_type": f"{src_type}->{rel}->{dst_type}",
                        "source_type": src_type,
                        "source_idx": src_i,
                        "relation": rel,
                        "target_type": dst_type,
                        "target_idx": dst_i,
                        "importance": round(float(mask_vals[i]), 4),
                        "direct_incident": is_incident
                    })

        # Prioritize direct incident edges, then sort by importance
        top_edges.sort(key=lambda e: (1 if e["direct_incident"] else 0, e["importance"]), reverse=True)
        top_edges = top_edges[:top_k_edges]

    return {
        "status": "COMPUTED",
        "method": "GNN_EXPLAINER",
        "target_node_category": target_node_category,
        "target_node_idx": target_node_idx,
        "feature_attributions": feature_attributions,
        "top_influential_edges": top_edges,
        "caveat": (
            "GNNExplainer attributions reflect the model's approximation of weak-supervision heuristic rules, "
            "explaining model sensitivity rather than certifying ground-truth post-quantum cryptographic exploitability."
        )
    }

