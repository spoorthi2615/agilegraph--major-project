import pytest
import torch
from src.ml.features import FeatureConfig, extract_node_features, extract_target_label, LabelSource

def test_feature_extraction_without_base_risk():
    props = {
        "risk_factors": {"data_sensitivity": 0.5, "crypto_weakness": 0.9},
        "base_risk": 0.75
    }
    config = FeatureConfig(include_base_risk=False)
    feat = extract_node_features(props, config)
    
    assert feat.shape == (14,) # 7 factors + 7 masks
    assert abs(feat[0].item() - 0.5) < 1e-5
    assert abs(feat[3].item() - 0.9) < 1e-5
    assert abs(feat[4].item() - 0.0) < 1e-5
    
    # Check masks (indices 7 to 13)
    assert feat[7].item() == 0.0 # data_sensitivity is present
    assert feat[10].item() == 0.0 # crypto_weakness is present
    assert feat[11].item() == 1.0 # cve_risk is missing

def test_feature_extraction_with_base_risk():
    props = {
        "risk_factors": {"data_sensitivity": 0.5},
        "base_risk": 0.75
    }
    config = FeatureConfig(include_base_risk=True)
    feat = extract_node_features(props, config)
    
    assert feat.shape == (16,) # 8 factors + 8 masks
    assert feat[7].item() == 0.75 # base_risk is at index 7
    assert feat[15].item() == 0.0 # base_risk mask is at index 15

def test_feature_extraction_structure_only():
    props = {
        "risk_factors": {"crypto_weakness": 0.9, "library_centrality": 1.0},
        "base_risk": 0.9
    }
    config = FeatureConfig(structure_only=True)
    feat = extract_node_features(props, config)
    
    # Assert it returns a dummy feature of size 1 with no semantic crypto information
    assert feat.shape == (1,)
    assert feat[0].item() == 0.0
    
    # Ensure none of the semantic values leaked through
    feat_list = feat.tolist()
    assert 0.9 not in feat_list
    assert 1.0 not in feat_list

def test_ablation_independence():
    # Prove that changing semantic evidence explicitly changes normal features,
    # but does NOT change structure-only features.
    props_low_risk = {
        "risk_factors": {"crypto_weakness": 0.1, "library_centrality": 0.2},
        "base_risk": 0.1
    }
    props_high_risk = {
        "risk_factors": {"crypto_weakness": 1.0, "library_centrality": 0.9},
        "base_risk": 0.9
    }
    
    config_normal = FeatureConfig(structure_only=False)
    config_ablation = FeatureConfig(structure_only=True)
    
    # 1. Normal features MUST be different
    feat_low_norm = extract_node_features(props_low_risk, config_normal)
    feat_high_norm = extract_node_features(props_high_risk, config_normal)
    assert not torch.allclose(feat_low_norm, feat_high_norm), "Semantic features failed to change!"
    
    # 2. Ablation features MUST be identical
    feat_low_abl = extract_node_features(props_low_risk, config_ablation)
    feat_high_abl = extract_node_features(props_high_risk, config_ablation)
    assert torch.allclose(feat_low_abl, feat_high_abl), "Ablation leaked semantic features!"
    
    # 3. Ablation features MUST NOT contain the semantic values
    assert 0.1 not in feat_low_abl.tolist()
    assert 1.0 not in feat_low_abl.tolist()
    
def test_target_label_extraction_expert():
    props = {"expert_label": {"class_idx": 2, "confidence": 1.0}}
    label = extract_target_label(props)
    assert label.source == LabelSource.EXPERT
    assert label.class_idx == 2

def test_target_label_extraction_heuristic():
    props = {"heuristic_label": {"class_idx": 1, "confidence": 0.8}}
    label = extract_target_label(props)
    assert label.source == LabelSource.HEURISTIC
    assert label.class_idx == 1

def test_target_label_extraction_unknown():
    props = {}
    label = extract_target_label(props)
    assert label.source == LabelSource.UNKNOWN
    assert label.class_idx is None
