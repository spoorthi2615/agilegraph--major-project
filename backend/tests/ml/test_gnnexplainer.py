import pytest
import torch
from torch_geometric.data import HeteroData
from src.ml.gatv2 import create_hetero_gatv2
from src.ml.explainability import (
    explain_with_gnnexplainer,
    HeteroExplainerModelWrapper,
    explain_heuristic_decomposition
)
from src.risk.score import RiskScoreResult, FactorContribution, MissingDataPolicy


def test_hetero_explainer_wrapper():
    data = HeteroData()
    data['file'].x = torch.randn(4, 14)
    data['crypto_usage'].x = torch.ones(2, 1)
    data['file', 'uses_crypto', 'crypto_usage'].edge_index = torch.tensor([[0, 1], [0, 1]])
    data['crypto_usage', 'rev_uses_crypto', 'file'].edge_index = torch.tensor([[0, 1], [0, 1]])

    model = create_hetero_gatv2(data.metadata(), hidden_channels=8, out_channels=3)
    model.initialize_lazy_layers(data)

    wrapper = HeteroExplainerModelWrapper(model, target_nodetype='file')
    out = wrapper(data.x_dict, data.edge_index_dict)
    assert out.shape == (4, 3)


def test_explain_with_gnnexplainer_output_structure():
    data = HeteroData()
    data['file'].x = torch.randn(4, 14)
    data['crypto_usage'].x = torch.ones(2, 1)
    data['file', 'uses_crypto', 'crypto_usage'].edge_index = torch.tensor([[0, 1], [0, 1]])
    data['crypto_usage', 'rev_uses_crypto', 'file'].edge_index = torch.tensor([[0, 1], [0, 1]])

    model = create_hetero_gatv2(data.metadata(), hidden_channels=8, out_channels=3)
    model.initialize_lazy_layers(data)

    result = explain_with_gnnexplainer(
        model=model,
        pyg_data=data,
        target_node_category="file",
        target_node_idx=0,
        epochs=15,
        lr=0.02,
        top_k_edges=3
    )

    assert result["status"] == "COMPUTED"
    assert result["method"] == "GNN_EXPLAINER"
    assert result["target_node_category"] == "file"
    assert result["target_node_idx"] == 0
    assert len(result["feature_attributions"]) == 14
    assert "crypto_weakness" in [f["feature_name"] for f in result["feature_attributions"]]
    assert len(result["top_influential_edges"]) <= 3
    assert "caveat" in result
    assert "heuristic" in result["caveat"].lower()


def test_explain_with_gnnexplainer_invalid_node():
    data = HeteroData()
    data['file'].x = torch.randn(2, 14)
    data['crypto_usage'].x = torch.ones(1, 1)
    data['file', 'uses', 'crypto_usage'].edge_index = torch.tensor([[0], [0]])

    model = create_hetero_gatv2(data.metadata(), hidden_channels=8, out_channels=3)
    model.initialize_lazy_layers(data)

    with pytest.raises(IndexError):
        explain_with_gnnexplainer(model, data, target_node_category="file", target_node_idx=99)

    with pytest.raises(ValueError):
        explain_with_gnnexplainer(model, data, target_node_category="nonexistent_category", target_node_idx=0)

