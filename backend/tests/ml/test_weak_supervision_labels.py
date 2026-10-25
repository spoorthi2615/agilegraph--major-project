import pytest
import torch
from src.ml.features import (
    derive_heuristic_label, 
    extract_target_label, 
    extract_node_features,
    FeatureConfig, 
    LabelSource
)
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode
from src.ml.converter import convert_agilegraph_to_pyg
from src.ml.pipeline import TrainingPipeline, MissingLabelsError


def test_derive_heuristic_label_classes():
    """Verifies that continuous scores map to discrete 3-class tiers."""
    # Low class: < 0.30
    lbl_low = derive_heuristic_label(0.15)
    assert lbl_low["class_idx"] == 0
    assert lbl_low["confidence"] == 0.5
    
    # Boundary Low
    lbl_low_bound = derive_heuristic_label(0.299)
    assert lbl_low_bound["class_idx"] == 0

    # Medium class: 0.30 <= score < 0.60
    lbl_med_low = derive_heuristic_label(0.30)
    assert lbl_med_low["class_idx"] == 1
    
    lbl_med = derive_heuristic_label(0.45)
    assert lbl_med["class_idx"] == 1

    # High class: >= 0.60
    lbl_high_bound = derive_heuristic_label(0.60)
    assert lbl_high_bound["class_idx"] == 2
    
    lbl_high = derive_heuristic_label(0.85)
    assert lbl_high["class_idx"] == 2


def test_derive_heuristic_label_invalid_or_none():
    """Verifies that None or invalid scores return None, preserving missing/unrated state."""
    assert derive_heuristic_label(None) is None
    assert derive_heuristic_label(-0.1) is None
    assert derive_heuristic_label(1.5) is None
    assert derive_heuristic_label("invalid") is None


def test_extract_target_label_provenance():
    """Verifies that heuristic_label sets source to HEURISTIC and preserves confidence."""
    props = {"heuristic_label": {"class_idx": 1, "confidence": 0.5}}
    target = extract_target_label(props)
    assert target.class_idx == 1
    assert target.source == LabelSource.HEURISTIC
    assert target.confidence == 0.5

    # Missing label returns UNKNOWN with class_idx=None
    empty_target = extract_target_label({})
    assert empty_target.class_idx is None
    assert empty_target.source == LabelSource.UNKNOWN


def test_converter_populates_y_tensor():
    """Verifies that convert_agilegraph_to_pyg correctly populates y and label_sources."""
    ag = AgileGraph()
    ag.add_node(GraphNode(
        id="proj:low.py",
        category="file",
        properties={"heuristic_label": {"class_idx": 0, "confidence": 0.5}}
    ))
    ag.add_node(GraphNode(
        id="proj:high.py",
        category="file",
        properties={"heuristic_label": {"class_idx": 2, "confidence": 0.5}}
    ))
    ag.add_node(GraphNode(
        id="proj:unrated.py",
        category="file",
        properties={}
    ))

    config = FeatureConfig(include_base_risk=False)
    data = convert_agilegraph_to_pyg(ag, config)

    y = data["file"].y.tolist()
    assert y == [0, 2, -1]  # unrated asset is -1
    assert data["file"].label_sources == ["HEURISTIC", "HEURISTIC", "UNKNOWN"]


def test_target_leakage_prevention():
    """
    Verifies that when include_base_risk=False (default), base_risk is strictly
    excluded from the feature tensor x, preventing target leakage.
    """
    props = {
        "base_risk": 0.85,
        "risk_factors": {
            "data_sensitivity": 0.5,
            "crypto_weakness": 0.9
        }
    }

    # Strict no-leakage config
    config_clean = FeatureConfig(include_base_risk=False)
    feat_clean = extract_node_features(props, config_clean)
    # 7 factors + 7 masks = 14 dimensions
    assert feat_clean.shape[0] == 14
    # 0.85 must NOT be present in feat_clean
    assert not any(abs(v - 0.85) < 1e-4 for v in feat_clean.tolist())

    # Positive control: when include_base_risk=True, dimension expands to 16 and includes base_risk
    config_leak = FeatureConfig(include_base_risk=True)
    feat_leak = extract_node_features(props, config_leak)
    assert feat_leak.shape[0] == 16
    assert any(abs(v - 0.85) < 1e-4 for v in feat_leak.tolist())


def test_training_pipeline_accepts_weak_labels():
    """Verifies that TrainingPipeline validates data when heuristic labels are present."""
    ag = AgileGraph()
    ag.add_node(GraphNode(
        id="proj:f1.py",
        category="file",
        properties={"heuristic_label": {"class_idx": 1, "confidence": 0.5}}
    ))
    data = convert_agilegraph_to_pyg(ag, FeatureConfig(include_base_risk=False))

    pipeline = TrainingPipeline(None, {})
    # Should not raise MissingLabelsError
    pipeline.validate_data_for_training(data)

    # Should raise MissingLabelsError on empty graph with no labels
    ag_empty = AgileGraph()
    ag_empty.add_node(GraphNode(id="proj:none.py", category="file", properties={}))
    data_empty = convert_agilegraph_to_pyg(ag_empty, FeatureConfig(include_base_risk=False))
    with pytest.raises(MissingLabelsError):
        pipeline.validate_data_for_training(data_empty)
