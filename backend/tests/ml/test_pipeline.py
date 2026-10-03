import pytest
import torch
import torch.nn as nn
from src.ml.pipeline import TrainingPipeline, MissingLabelsError, set_seed
from torch_geometric.data import HeteroData

class DummyModel(nn.Module):
    def forward(self, x_dict, edge_index_dict):
        out = {}
        for k, v in x_dict.items():
            out[k] = torch.zeros((v.shape[0], 3), requires_grad=True)
        return out

def test_pipeline_refuses_training_without_labels():
    model = DummyModel()
    pipeline = TrainingPipeline(model, config={"seed": 42})
    
    data = HeteroData()
    data["file"].x = torch.randn((2, 14))
    data["file"].y = torch.tensor([-1, -1]) # No labels
    
    with pytest.raises(MissingLabelsError, match="No labeled data found"):
        pipeline.validate_data_for_training(data)

def test_pipeline_accepts_training_with_labels():
    model = DummyModel()
    pipeline = TrainingPipeline(model, config={"seed": 42})
    
    data = HeteroData()
    data["file"].x = torch.randn((2, 14))
    data["file"].y = torch.tensor([-1, 1]) # One valid label
    
    # Should not raise exception
    pipeline.validate_data_for_training(data)

def test_deterministic_seed():
    set_seed(42)
    a = torch.randn(1).item()
    set_seed(42)
    b = torch.randn(1).item()
    assert a == b
