import pytest
from src.ml.expert_validation import ValidationDataset, AssetForReview, ValidationSession, ExpertLabel, ExpertLabelClass, AggregationMethod

def test_expert_schema():
    # SYNTHETIC_TEST_DATA
    # NOT REAL EXPERT VALIDATION
    
    asset = AssetForReview(asset_id="f1", project_id="proj_a")
    lbl1 = ExpertLabel(asset_id="f1", project_id="proj_a", expert_id="e1", label=ExpertLabelClass.HIGH, dataset_version="v1", annotation_protocol_version="v1")
    lbl2 = ExpertLabel(asset_id="f1", project_id="proj_a", expert_id="e2", label=ExpertLabelClass.MEDIUM, dataset_version="v1", annotation_protocol_version="v1")
    lbl3 = ExpertLabel(asset_id="f1", project_id="proj_a", expert_id="e3", label=ExpertLabelClass.HIGH, dataset_version="v1", annotation_protocol_version="v1")
    
    s1 = ValidationSession(session_id="s1", expert_id="e1", labels=[lbl1])
    s2 = ValidationSession(session_id="s2", expert_id="e2", labels=[lbl2])
    s3 = ValidationSession(session_id="s3", expert_id="e3", labels=[lbl3])
    
    ds = ValidationDataset(dataset_version="v1", annotation_protocol_version="v1", assets=[asset], sessions=[s1, s2, s3])
    
    assert len(ds.sessions) == 3
    consensus = ds.get_consensus("f1", AggregationMethod.MAJORITY_VOTE)
    assert consensus == ExpertLabelClass.HIGH
    
def test_expert_schema_missing_and_ties():
    # SYNTHETIC_TEST_DATA
    # NOT REAL EXPERT VALIDATION
    
    asset = AssetForReview(asset_id="f1", project_id="proj_a")
    lbl1 = ExpertLabel(asset_id="f1", project_id="proj_a", expert_id="e1", label=ExpertLabelClass.HIGH, dataset_version="v1", annotation_protocol_version="v1")
    lbl2 = ExpertLabel(asset_id="f1", project_id="proj_a", expert_id="e2", label=ExpertLabelClass.MEDIUM, dataset_version="v1", annotation_protocol_version="v1")
    
    s1 = ValidationSession(session_id="s1", expert_id="e1", labels=[lbl1])
    s2 = ValidationSession(session_id="s2", expert_id="e2", labels=[lbl2])
    
    ds = ValidationDataset(dataset_version="v1", annotation_protocol_version="v1", assets=[asset], sessions=[s1, s2])
    
    # Tie results in None
    assert ds.get_consensus("f1", AggregationMethod.MAJORITY_VOTE) is None
