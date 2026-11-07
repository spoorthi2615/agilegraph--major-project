import pytest
import numpy as np
from src.ml.expert_validation import (
    Expert,
    AssetForReview,
    ExpertLabel,
    ExpertLabelClass,
    ValidationDataset,
    LABEL_TO_INT
)
from src.ml.agreement import AgreementMetrics


def test_expert_dataset_adjudication():
    e1 = Expert(expert_id="exp_1", name="Expert One", years_experience=8)
    e2 = Expert(expert_id="exp_2", name="Expert Two", years_experience=5)
    e3 = Expert(expert_id="exp_3", name="Expert Three", years_experience=10)

    asset1 = AssetForReview(asset_id="file_rsa.py", repository="repo1", file_path="src/rsa.py")
    asset2 = AssetForReview(asset_id="file_aes.py", repository="repo1", file_path="src/aes.py")

    labels = [
        # asset1: 2 HIGH, 1 MEDIUM -> majority HIGH
        ExpertLabel(asset_id="file_rsa.py", expert_id="exp_1", label=ExpertLabelClass.HIGH),
        ExpertLabel(asset_id="file_rsa.py", expert_id="exp_2", label=ExpertLabelClass.HIGH),
        ExpertLabel(asset_id="file_rsa.py", expert_id="exp_3", label=ExpertLabelClass.MEDIUM),
        # asset2: 3 LOW -> unanimous LOW
        ExpertLabel(asset_id="file_aes.py", expert_id="exp_1", label=ExpertLabelClass.LOW),
        ExpertLabel(asset_id="file_aes.py", expert_id="exp_2", label=ExpertLabelClass.LOW),
        ExpertLabel(asset_id="file_aes.py", expert_id="exp_3", label=ExpertLabelClass.LOW),
    ]

    dataset = ValidationDataset(
        experts=[e1, e2, e3],
        assets=[asset1, asset2],
        labels=labels
    )

    adjudicated = dataset.adjudicate(strategy="MAJORITY")
    assert len(adjudicated) == 2

    adj1 = next(a for a in adjudicated if a.asset_id == "file_rsa.py")
    assert adj1.consensus_label == ExpertLabelClass.HIGH
    assert adj1.agreement_score == round(2 / 3, 4)
    assert adj1.adjudication_method == "MAJORITY"

    adj2 = next(a for a in adjudicated if a.asset_id == "file_aes.py")
    assert adj2.consensus_label == ExpertLabelClass.LOW
    assert adj2.agreement_score == 1.0
    assert adj2.adjudication_method == "UNANIMOUS"


def test_cohens_kappa_perfect_and_weighted():
    rater1 = [0, 1, 2, 0, 1, 2]
    rater2 = [0, 1, 2, 0, 1, 2]
    k_perfect = AgreementMetrics.cohens_kappa(rater1, rater2, weights="linear")
    assert k_perfect == 1.0

    # Mild discordance (adjacent classes: 0 vs 1)
    rater3 = [0, 1, 2, 0, 1, 1]
    k_linear = AgreementMetrics.cohens_kappa(rater1, rater3, weights="linear")
    assert 0.5 < k_linear < 1.0


def test_fleiss_kappa_calculation():
    # 4 subjects, 3 categories, 3 raters per subject
    # Subject 1: unanimous category 0 (3, 0, 0)
    # Subject 2: unanimous category 1 (0, 3, 0)
    # Subject 3: unanimous category 2 (0, 0, 3)
    # Subject 4: unanimous category 0 (3, 0, 0)
    matrix_perfect = np.array([
        [3, 0, 0],
        [0, 3, 0],
        [0, 0, 3],
        [3, 0, 0]
    ])
    k_fleiss = AgreementMetrics.fleiss_kappa(matrix_perfect)
    assert k_fleiss == 1.0

    # Test error handling on inconsistent raters
    matrix_invalid = np.array([
        [3, 0, 0],
        [2, 0, 0]  # only 2 raters
    ])
    with pytest.raises(ValueError):
        AgreementMetrics.fleiss_kappa(matrix_invalid)


def test_macro_f1_and_bootstrap_ci():
    y_true = [0, 1, 2, 0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 2, 0, 2, 2, 0, 1, 1]

    f1 = AgreementMetrics.macro_f1(y_true, y_pred)
    assert 0.0 <= f1 <= 1.0

    ci = AgreementMetrics.bootstrap_confidence_interval(
        metric_fn=AgreementMetrics.macro_f1,
        y_true=y_true,
        y_pred=y_pred,
        n_bootstraps=200,
        confidence_level=0.95,
        seed=42
    )

    assert ci["ci_lower"] <= ci["point_estimate"] <= ci["ci_upper"]
    assert ci["n_bootstraps"] == 200


def test_pairwise_kappas():
    raters = {
        "exp_a": [0, 1, 2, 0, 2],
        "exp_b": [0, 1, 2, 1, 2],
        "exp_c": [0, 1, 2, 0, 2]
    }
    res = AgreementMetrics.pairwise_kappas(raters, weights="linear")
    assert res["num_pairs"] == 3
    assert "exp_a_vs_exp_b" in res["pairwise"]
    assert res["mean_pairwise_kappa"] > 0.6


def test_real_submission_json_pipeline(tmp_path):
    import json
    from scripts.run_expert_validation import load_submitted_annotations

    sub1 = {
        "expert_profile": {"expert_id": "EXP_01", "name": "Alice", "years_experience": 10},
        "annotations": [
            {"asset_id": "file_a.py", "repository": "r1", "assigned_risk_category": "HIGH", "confidence": 0.9},
            {"asset_id": "file_b.py", "repository": "r1", "assigned_risk_category": "LOW", "confidence": 0.8}
        ]
    }
    sub2 = {
        "expert_profile": {"expert_id": "EXP_02", "name": "Bob", "years_experience": 7},
        "annotations": [
            {"asset_id": "file_a.py", "repository": "r1", "assigned_risk_category": "HIGH", "confidence": 0.95},
            {"asset_id": "file_b.py", "repository": "r1", "assigned_risk_category": "MEDIUM", "confidence": 0.7}
        ]
    }

    p1 = tmp_path / "exp01.json"
    p2 = tmp_path / "exp02.json"
    p1.write_text(json.dumps(sub1), encoding="utf-8")
    p2.write_text(json.dumps(sub2), encoding="utf-8")

    loaded = load_submitted_annotations(tmp_path)
    assert len(loaded) == 2

    # Verify building dataset and adjudicating
    experts = [Expert(expert_id=s["expert_profile"]["expert_id"]) for s in loaded]
    labels = []
    for s in loaded:
        e_id = s["expert_profile"]["expert_id"]
        for a in s["annotations"]:
            labels.append(ExpertLabel(
                asset_id=a["asset_id"],
                expert_id=e_id,
                label=ExpertLabelClass[a["assigned_risk_category"]]
            ))

    assets = [AssetForReview(asset_id="file_a.py", repository="r1", file_path="file_a.py"),
              AssetForReview(asset_id="file_b.py", repository="r1", file_path="file_b.py")]

    dataset = ValidationDataset(experts=experts, assets=assets, labels=labels)
    adj = dataset.adjudicate()
    assert len(adj) == 2
    adj_a = next(x for x in adj if x.asset_id == "file_a.py")
    assert adj_a.consensus_label == ExpertLabelClass.HIGH
    assert adj_a.adjudication_method == "UNANIMOUS"


def test_validation_dataset_deduplication():
    """Verify that multiple annotations from the same expert on the same canonical asset are cleanly deduplicated."""
    e1 = Expert(expert_id="exp_1", name="Expert One", years_experience=8)
    a1 = AssetForReview(asset_id="r1:rsa.go", repository="r1", file_path="rsa.go")

    # Expert 1 rated r1:rsa.go twice in the same repository
    labels = [
        ExpertLabel(asset_id="rsa.go", expert_id="exp_1", label=ExpertLabelClass.HIGH, confidence=0.85, repository="r1"),
        ExpertLabel(asset_id="rsa.go", expert_id="exp_1", label=ExpertLabelClass.HIGH, confidence=0.95, repository="r1"),
    ]

    dataset = ValidationDataset(
        experts=[e1],
        assets=[a1],
        labels=labels
    )
    assert len(dataset.labels) == 2

    removed = dataset.deduplicate_labels()
    assert removed == 1
    assert len(dataset.labels) == 1
    assert dataset.labels[0].confidence == 0.95
    assert dataset.labels[0].label == ExpertLabelClass.HIGH

    # Adjudication works cleanly with exactly 1 vote
    adj = dataset.adjudicate()
    assert len(adj) == 1
    assert adj[0].consensus_label == ExpertLabelClass.HIGH
    assert adj[0].adjudication_method == "UNANIMOUS"


def test_repository_scoped_asset_identity_preservation():
    """Verify that identical filenames across different repositories remain separate assets."""
    e1 = Expert(expert_id="exp_1", name="Expert One", years_experience=8)
    
    # Same relative filename 'ecdsa.go' across go_jwt and go_jwt_go
    a_jwt = AssetForReview(asset_id="go_jwt:ecdsa.go", repository="go_jwt", file_path="ecdsa.go")
    a_jwt_go = AssetForReview(asset_id="go_jwt_go:ecdsa.go", repository="go_jwt_go", file_path="ecdsa.go")

    labels = [
        ExpertLabel(asset_id="ecdsa.go", expert_id="exp_1", label=ExpertLabelClass.HIGH, confidence=0.9, repository="go_jwt"),
        ExpertLabel(asset_id="ecdsa.go", expert_id="exp_1", label=ExpertLabelClass.HIGH, confidence=0.95, repository="go_jwt_go"),
    ]

    dataset = ValidationDataset(
        experts=[e1],
        assets=[a_jwt, a_jwt_go],
        labels=labels
    )
    assert len(dataset.labels) == 2

    # Deduplication must NOT merge them because repositories differ
    removed = dataset.deduplicate_labels()
    assert removed == 0
    assert len(dataset.labels) == 2

    # Both remain distinct in adjudication
    adj = dataset.adjudicate()
    assert len(adj) == 2
    adj_ids = {a.asset_id for a in adj}
    assert adj_ids == {"go_jwt:ecdsa.go", "go_jwt_go:ecdsa.go"}


def test_conflicting_duplicate_labels_conservative_precedence():
    """Verify that conflicting duplicate ratings for the same canonical asset are conservatively resolved."""
    e1 = Expert(expert_id="exp_1", name="Expert One", years_experience=8)
    a1 = AssetForReview(asset_id="r1:cipher.go", repository="r1", file_path="cipher.go")

    # Expert submitted LOW first, but later marked HIGH for the same canonical asset
    labels = [
        ExpertLabel(asset_id="cipher.go", expert_id="exp_1", label=ExpertLabelClass.LOW, confidence=0.7, rationale="thought it was safe", repository="r1"),
        ExpertLabel(asset_id="cipher.go", expert_id="exp_1", label=ExpertLabelClass.HIGH, confidence=0.9, rationale="re-evaluated: uses broken cipher", repository="r1"),
    ]

    dataset = ValidationDataset(
        experts=[e1],
        assets=[a1],
        labels=labels
    )

    removed = dataset.deduplicate_labels()
    assert removed == 1
    assert len(dataset.labels) == 1
    # Conservative resolution: HIGH takes precedence over LOW
    assert dataset.labels[0].label == ExpertLabelClass.HIGH
    assert dataset.labels[0].confidence == 0.9
    assert "re-evaluated: uses broken cipher" in dataset.labels[0].rationale




