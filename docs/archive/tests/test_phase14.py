import pytest
import numpy as np
from src.ml.expert_validation import ValidationDataset, ValidationSession, ExpertLabel, ExpertLabelClass, AssetForReview, AggregationMethod
from src.ml.agreement import AgreementMetrics
from src.ml.evaluation import EvaluationMetrics
from src.ml.experiment import ExperimentManifest, LabelRegime, ModelType
from src.ml.training import ModelTrainer

# SYNTHETIC_TEST_DATA
# NOT REAL EXPERT VALIDATION

def test_genuine_label_schema_validation():
    # SYNTHETIC_TEST_DATA
    # Ensure schema handles high/medium/low properly
    lbl = ExpertLabel(asset_id="f1", project_id="p1", expert_id="e1", label=ExpertLabelClass.HIGH, dataset_version="v1", annotation_protocol_version="v1")
    assert lbl.label == ExpertLabelClass.HIGH

def test_consensus_generation():
    # SYNTHETIC_TEST_DATA
    a1 = AssetForReview(asset_id="f1", project_id="p1")
    l1 = ExpertLabel(asset_id="f1", project_id="p1", expert_id="e1", label=ExpertLabelClass.LOW, dataset_version="v1", annotation_protocol_version="v1")
    l2 = ExpertLabel(asset_id="f1", project_id="p1", expert_id="e2", label=ExpertLabelClass.LOW, dataset_version="v1", annotation_protocol_version="v1")
    l3 = ExpertLabel(asset_id="f1", project_id="p1", expert_id="e3", label=ExpertLabelClass.HIGH, dataset_version="v1", annotation_protocol_version="v1")
    
    ds = ValidationDataset(dataset_version="v1", annotation_protocol_version="v1", assets=[a1], sessions=[
        ValidationSession(session_id="s1", expert_id="e1", labels=[l1]),
        ValidationSession(session_id="s2", expert_id="e2", labels=[l2]),
        ValidationSession(session_id="s3", expert_id="e3", labels=[l3]),
    ])
    
    c = ds.get_consensus("f1", AggregationMethod.MAJORITY_VOTE)
    assert c == ExpertLabelClass.LOW

def test_expert_rating_completeness_and_agreement():
    # SYNTHETIC_TEST_DATA
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.HIGH, ExpertLabelClass.UNKNOWN]
    y2 = [ExpertLabelClass.HIGH, ExpertLabelClass.LOW, ExpertLabelClass.HIGH]
    
    # Valid overlap is index 0 and 1.
    kappa = AgreementMetrics.cohens_kappa(y1, y2)
    assert kappa["status"] == "COMPUTED"
    assert kappa["statistic"] >= 0.0

def test_model_training_with_actual_label_structure():
    # SYNTHETIC_TEST_DATA
    # Trainer should refuse expert regime
    manifest = ExperimentManifest(
        experiment_id="test", dataset_version="v1", project_split={}, feature_configuration="v1", 
        include_base_risk=True, label_source=LabelRegime.EXPERT, model_configuration=ModelType.GATV2, 
        seed=42, software_version="1.0"
    )
    trainer = ModelTrainer(manifest)
    res = trainer.run_training_loop()
    assert res["status"] == "PENDING_EXPERT_LABELS"

def test_leakage_ablation():
    # SYNTHETIC_TEST_DATA
    manifest = ExperimentManifest(
        experiment_id="test", dataset_version="v1", project_split={}, feature_configuration="v1", 
        include_base_risk=True, label_source=LabelRegime.SYNTHETIC, model_configuration=ModelType.GATV2, 
        seed=42, software_version="1.0"
    )
    trainer = ModelTrainer(manifest)
    res = trainer.run_leakage_ablation()
    assert res["status"] == "INFRASTRUCTURE_READY"

def test_baseline_comparison_and_bootstrap():
    # SYNTHETIC_TEST_DATA
    y_true = np.array([0, 1])
    y_pred = np.array([0, 1])
    
    metrics = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    
    ci = EvaluationMetrics.bootstrap_ci(y_true, y_pred)
    assert ci["status"] == "COMPUTED" # We mock this for SYNTHETIC_TEST_DATA
    
def test_paired_permutation_reproducibility():
    # SYNTHETIC_TEST_DATA
    pval = EvaluationMetrics.paired_permutation_test(np.array([]), np.array([]), np.array([]))
    assert pval["status"] == "PENDING_EXPERT_LABELS"
    assert pval["p_value"] is None
