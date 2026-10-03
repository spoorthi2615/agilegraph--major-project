import pytest
import torch
from src.ml.gatv2 import create_hetero_gatv2

def test_gatv2_initialization():
    # Synthetic metadata for the model
    metadata = (
        ["file", "library"],
        [("file", "IMPORTS", "library"), ("library", "IMPORTED_BY", "file")]
    )
    
    # 14 input features (7 factors + 7 masks)
    model = create_hetero_gatv2(metadata, hidden_channels=16, out_channels=3, num_heads=2)
    assert model is not None
    
def test_gatv2_forward_pass_shapes():
    metadata = (
        ["file", "library"],
        [("file", "IMPORTS", "library"), ("library", "IMPORTED_BY", "file")]
    )
    model = create_hetero_gatv2(metadata, hidden_channels=16, out_channels=3, num_heads=2)
    
    x_dict = {
        "file": torch.randn((2, 14)),
        "library": torch.randn((1, 14))
    }
    edge_index_dict = {
        ("file", "IMPORTS", "library"): torch.tensor([[0, 1], [0, 0]], dtype=torch.long),
        ("library", "IMPORTED_BY", "file"): torch.tensor([[0, 0], [0, 1]], dtype=torch.long)
    }
    
    out = model(x_dict, edge_index_dict)
    
    assert "file" in out
    assert "library" in out
    assert out["file"].shape == (2, 3)
    assert out["library"].shape == (1, 3)

def test_gatv2_six_categories_regression():
    # Covers file, cryptousage, certificate, endpoint, library, sensitivedata
    metadata = (
        ["file", "cryptousage", "certificate", "endpoint", "library", "sensitivedata"],
        [
            ("file", "IMPORTS", "library"),
            ("file", "USES", "cryptousage"),
            ("endpoint", "HAS", "certificate"),
            ("file", "ACCESSES", "sensitivedata")
        ]
    )
    model = create_hetero_gatv2(metadata, hidden_channels=8, out_channels=3, num_heads=2)
    
    x_dict = {
        "file": torch.randn((2, 14)),
        "cryptousage": torch.randn((1, 14)),
        "certificate": torch.randn((1, 14)),
        "endpoint": torch.randn((1, 14)),
        "library": torch.randn((1, 14)),
        "sensitivedata": torch.randn((1, 14))
    }
    
    edge_index_dict = {
        ("file", "IMPORTS", "library"): torch.tensor([[0], [0]], dtype=torch.long),
        ("file", "USES", "cryptousage"): torch.tensor([[1], [0]], dtype=torch.long),
        ("endpoint", "HAS", "certificate"): torch.tensor([[0], [0]], dtype=torch.long),
        ("file", "ACCESSES", "sensitivedata"): torch.tensor([[0], [0]], dtype=torch.long)
    }
    
    # Asymmetric: certificate, cryptousage, library, sensitivedata only receive messages.
    # endpoint only sends messages.
    # file sends messages.
    
    out = model(x_dict, edge_index_dict)
    
    for category in metadata[0]:
        assert category in out
        if category == "file":
            assert out[category].shape == (2, 3)
        else:
            assert out[category].shape == (1, 3)
