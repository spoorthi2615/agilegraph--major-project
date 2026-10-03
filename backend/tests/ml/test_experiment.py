import pytest
from src.ml.experiment import ExperimentManifest, LabelRegime, ModelType, AblationRegime
from src.ml.training import ModelTrainer

def test_manifest_completeness():
    manifest = ExperimentManifest(
        experiment_id="test_exp",
        dataset_version="v1",
        project_split={"train": ["a"], "val": ["b"], "test": ["c"]},
        feature_configuration="test_cfg",
        include_base_risk=True,
        label_source=LabelRegime.SYNTHETIC,
        model_configuration=ModelType.GATV2,
        seed=42,
        software_version="1.0"
    )
    assert manifest.experiment_id == "test_exp"
    assert manifest.include_base_risk is True
    assert manifest.label_source == LabelRegime.SYNTHETIC

def test_training_refusal_without_expert_labels():
    manifest = ExperimentManifest(
        experiment_id="test_exp",
        dataset_version="v1",
        project_split={"train": ["a"], "val": ["b"], "test": ["c"]},
        feature_configuration="test_cfg",
        include_base_risk=True,
        label_source=LabelRegime.EXPERT,
        model_configuration=ModelType.GATV2,
        seed=42,
        software_version="1.0"
    )
    trainer = ModelTrainer(manifest)
    res = trainer.run_training_loop()
    assert res["status"] == "PENDING_EXPERT_LABELS"
    
def test_synthetic_smoke_test():
    manifest = ExperimentManifest(
        experiment_id="test_exp",
        dataset_version="v1",
        project_split={"train": ["a"], "val": ["b"], "test": ["c"]},
        feature_configuration="test_cfg",
        include_base_risk=True,
        label_source=LabelRegime.SYNTHETIC,
        model_configuration=ModelType.GATV2,
        seed=42,
        software_version="1.0"
    )
    trainer = ModelTrainer(manifest)
    res = trainer.run_training_loop()
    assert res["status"] == "INFRASTRUCTURE_VALIDATED_SYNTHETIC"

def test_leakage_ablation_infrastructure():
    manifest = ExperimentManifest(
        experiment_id="test_exp",
        dataset_version="v1",
        project_split={"train": ["a"], "val": ["b"], "test": ["c"]},
        feature_configuration="test_cfg",
        include_base_risk=True, # WITH_BASE_RISK
        label_source=LabelRegime.SYNTHETIC,
        model_configuration=ModelType.GATV2,
        seed=42,
        software_version="1.0"
    )
    trainer = ModelTrainer(manifest)
    res = trainer.run_leakage_ablation()
    assert res["status"] == "INFRASTRUCTURE_READY"
