"""
Regression test suite for AgileGraph Step 4 — Independent Expert Annotation Framework.
Tests schema validation, sampling determinism, blinding enforcement,
import validation rules, and inter-annotator agreement metrics (Cohen's, Fleiss', Krippendorff's).
"""

import os
import json
import pytest
import numpy as np
from src.ml.expert_validation import (
    ExpertLabel,
    ExpertLabelClass,
    CryptoConcern,
    SensitiveDataImpact,
    ExposureLevel,
    PostQuantumUrgency,
    EvidenceConfidence,
    AnnotationStatus,
    AdjudicatedLabel,
    AggregationMethod,
    AssetForReview,
    ValidationSession,
    ValidationDataset,
)
from src.ml.import_annotations import AnnotationImporter
from src.ml.agreement import AgreementMetrics
from scripts.generate_annotation_package import generate_expert_annotation_package


def test_expert_label_schema_multidimensional():
    """Verify that ExpertLabel supports all 7 rubric dimensions and handles aliases cleanly."""
    lbl = ExpertLabel(
        asset_id="proj:file.py",
        project_id="proj",
        expert_id="expert_01",
        label=ExpertLabelClass.HIGH,
        crypto_concern=CryptoConcern.CLASSICAL_VULNERABLE_PQC,
        sensitive_data_impact=SensitiveDataImpact.CREDENTIALS_OR_SECRETS,
        exposure=ExposureLevel.INTERNET_FACING,
        post_quantum_urgency=PostQuantumUrgency.IMMEDIATE_ACTION,
        evidence_confidence=EvidenceConfidence.HIGH,
        rationale="RSA-2048 key exchange vulnerable to Shor's algorithm.",
        rubric_version="2.0.0"
    )
    assert lbl.label == ExpertLabelClass.HIGH
    assert lbl.crypto_concern == CryptoConcern.CLASSICAL_VULNERABLE_PQC
    assert lbl.sensitive_data_impact == SensitiveDataImpact.CREDENTIALS_OR_SECRETS
    assert lbl.exposure == ExposureLevel.INTERNET_FACING
    assert lbl.post_quantum_urgency == PostQuantumUrgency.IMMEDIATE_ACTION
    assert lbl.evidence_confidence == EvidenceConfidence.HIGH
    assert "Shor's algorithm" in lbl.rationale

    # Test alias mapping (migration_priority -> label, annotator_id -> expert_id)
    lbl_alias = ExpertLabel.model_validate({
        "asset_id": "proj:file2.py",
        "project_id": "proj",
        "annotator_id": "expert_02",
        "migration_priority": "MEDIUM",
        "dataset_version": "v1",
        "annotation_protocol_version": "2.0.0"
    })
    assert lbl_alias.expert_id == "expert_02"
    assert lbl_alias.label == ExpertLabelClass.MEDIUM


def test_adjudicated_label_schema_separation():
    """Verify that AdjudicatedLabel stores consensus separately while preserving original labels."""
    orig1 = ExpertLabel(asset_id="a1", project_id="p1", expert_id="e1", label=ExpertLabelClass.HIGH)
    orig2 = ExpertLabel(asset_id="a1", project_id="p1", expert_id="e2", label=ExpertLabelClass.MEDIUM)

    adj = AdjudicatedLabel(
        asset_id="a1",
        project_id="p1",
        adjudicated_priority=ExpertLabelClass.HIGH,
        adjudicator_id="lead_adjudicator",
        original_expert_labels=[orig1, orig2],
        adjudication_rationale="Review confirmed long-term retention of RSA signature keys.",
        adjudication_method=AggregationMethod.ADJUDICATION
    )
    assert adj.adjudicated_priority == ExpertLabelClass.HIGH
    assert len(adj.original_expert_labels) == 2
    assert adj.original_expert_labels[0].label == ExpertLabelClass.HIGH
    assert adj.original_expert_labels[1].label == ExpertLabelClass.MEDIUM


def test_sampling_determinism_and_blinding(tmp_path):
    """
    Verify that annotation package generation is deterministic and strictly blinds annotators
    by omitting heuristic scores and model predictions.
    """
    out_pkg1 = str(tmp_path / "pkg1.json")
    out_pkg2 = str(tmp_path / "pkg2.json")

    pkg1 = generate_expert_annotation_package(out_path=out_pkg1, seed=42)
    pkg2 = generate_expert_annotation_package(out_path=out_pkg2, seed=42)

    # Identical asset list
    assert len(pkg1["assets"]) == len(pkg2["assets"]) == 166
    assert [a["asset_id"] for a in pkg1["assets"]] == [a["asset_id"] for a in pkg2["assets"]]

    # Verify STRICT BLINDING: no heuristic scores or predictions in any dossier
    for asset in pkg1["assets"]:
        assert "heuristic_score" not in asset
        assert "score" not in asset
        assert "prediction" not in asset
        assert "factors" not in asset  # Internal scoring factors omitted
        assert "observable_evidence" in asset  # Code evidence preserved


def test_importer_validations_and_rejections(tmp_path):
    """Verify that AnnotationImporter rejects invalid submissions and accepts conformant data."""
    importer = AnnotationImporter(
        expected_asset_ids=["asset_01", "asset_02"],
        expected_expert_ids=["expert_01", "expert_02"],
        dataset_version="v1",
        expected_protocol_version="2.0.0",
        allow_legacy_without_provenance=True
    )

    # 1. Reject when protocol is not finalized
    res_unfinalized = importer.import_annotations("dummy.json", protocol_status="PENDING_FINALIZATION")
    assert res_unfinalized["status"] == "REJECTED"
    assert "Cannot import" in res_unfinalized["message"]

    # 2. Reject unknown asset ID
    bad_asset_file = str(tmp_path / "bad_asset.json")
    with open(bad_asset_file, "w") as f:
        json.dump({"labels": [{
            "asset_id": "unknown_asset", "expert_id": "expert_01", "label": "HIGH",
            "timestamp": "2026-10-11T00:00:00Z", "dataset_version": "v1"
        }]}, f)
    res_bad_asset = importer.import_annotations(bad_asset_file, protocol_status="FINALIZED")
    assert res_bad_asset["status"] == "REJECTED"
    assert "Unknown asset ID" in res_bad_asset["message"]

    # 3. Reject duplicate rating by same expert
    dup_file = str(tmp_path / "dup.json")
    with open(dup_file, "w") as f:
        json.dump({"labels": [
            {"asset_id": "asset_01", "expert_id": "expert_01", "label": "HIGH", "timestamp": "2026-10-11T00:00:00Z", "dataset_version": "v1"},
            {"asset_id": "asset_01", "expert_id": "expert_01", "label": "LOW", "timestamp": "2026-10-11T00:01:00Z", "dataset_version": "v1"}
        ]}, f)
    res_dup = importer.import_annotations(dup_file, protocol_status="FINALIZED")
    assert res_dup["status"] == "REJECTED"
    assert "Duplicate rating" in res_dup["message"]

    # 4. Reject invalid category enum value
    bad_cat_file = str(tmp_path / "bad_cat.json")
    with open(bad_cat_file, "w") as f:
        json.dump({"labels": [{
            "asset_id": "asset_01", "expert_id": "expert_01", "label": "HIGH",
            "crypto_concern": "INVALID_CRYPTO_CATEGORY",
            "timestamp": "2026-10-11T00:00:00Z", "dataset_version": "v1"
        }]}, f)
    res_bad_cat = importer.import_annotations(bad_cat_file, protocol_status="FINALIZED")
    assert res_bad_cat["status"] == "REJECTED"
    assert "Invalid crypto_concern" in res_bad_cat["message"]

    # 5. Handle missing responses / partial ratings safely (allowing UNKNOWN)
    partial_file = str(tmp_path / "partial.json")
    with open(partial_file, "w") as f:
        json.dump({"labels": [{
            "asset_id": "asset_01", "expert_id": "expert_01", "label": "UNKNOWN",
            "crypto_concern": "UNKNOWN_OR_UNCLASSIFIED",
            "sensitive_data_impact": "UNKNOWN_OR_INSUFFICIENT_EVIDENCE",
            "exposure": "UNKNOWN",
            "post_quantum_urgency": "INVESTIGATE_FURTHER",
            "evidence_confidence": "LOW",
            "rationale": "Insufficient context in file.",
            "timestamp": "2026-10-11T00:00:00Z", "dataset_version": "v1",
            "annotation_protocol_version": "2.0.0"
        }]}, f)
    res_partial = importer.import_annotations(partial_file, protocol_status="FINALIZED")
    assert res_partial["status"] == "SUCCESS"
    assert res_partial["imported_count"] == 1
    assert res_partial["labels"][0].label == ExpertLabelClass.UNKNOWN

    # 6. Accept valid submission with multi-dimensional rubric fields and verify individual rating preservation
    valid_file = str(tmp_path / "valid.json")
    with open(valid_file, "w") as f:
        json.dump({
            "labels": [
                {
                    "asset_id": "asset_01",
                    "expert_id": "expert_01",
                    "label": "HIGH",
                    "crypto_concern": "CLASSICAL_VULNERABLE_PQC",
                    "sensitive_data_impact": "CREDENTIALS_OR_SECRETS",
                    "exposure": "INTERNET_FACING",
                    "post_quantum_urgency": "IMMEDIATE_ACTION",
                    "evidence_confidence": "HIGH",
                    "rationale": "Explicit RSA-2048 signing.",
                    "timestamp": "2026-10-11T00:00:00Z",
                    "dataset_version": "v1",
                    "annotation_protocol_version": "2.0.0"
                },
                {
                    "asset_id": "asset_01",
                    "expert_id": "expert_02",
                    "label": "MEDIUM",
                    "crypto_concern": "CLASSICAL_VULNERABLE_PQC",
                    "sensitive_data_impact": "CREDENTIALS_OR_SECRETS",
                    "exposure": "INTERNAL",
                    "post_quantum_urgency": "PLANNED_MIGRATION",
                    "evidence_confidence": "MEDIUM",
                    "rationale": "Internal signing only.",
                    "timestamp": "2026-10-11T00:00:00Z",
                    "dataset_version": "v1",
                    "annotation_protocol_version": "2.0.0"
                }
            ],
            "adjudicated_labels": [
                {
                    "asset_id": "asset_01",
                    "adjudicator_id": "lead_adjudicator",
                    "adjudicated_priority": "HIGH",
                    "adjudication_rationale": "Consensus confirmed RSA severity."
                }
            ]
        }, f)
    res_valid = importer.import_annotations(valid_file, protocol_status="FINALIZED")
    assert res_valid["status"] == "SUCCESS"
    assert res_valid["imported_count"] == 2
    assert res_valid["adjudicated_count"] == 1
    # Verify individual ratings remain intact and distinct from adjudicated consensus
    labels = res_valid["labels"]
    adjs = res_valid["adjudications"]
    assert labels[0].label == ExpertLabelClass.HIGH
    assert labels[1].label == ExpertLabelClass.MEDIUM
    assert adjs[0].adjudicated_priority == ExpertLabelClass.HIGH


def test_krippendorff_alpha_nominal_and_ordinal():
    """Verify Krippendorff's alpha handles multiple raters, perfect agreement, and missing data."""
    # 1. Perfect agreement across 3 raters on 4 items
    perfect_data = np.array([
        [0, 1, 2, 0],
        [0, 1, 2, 0],
        [0, 1, 2, 0]
    ])
    res_perf = AgreementMetrics.krippendorff_alpha(perfect_data, level="ordinal")
    assert res_perf["status"] == "COMPUTED"
    assert res_perf["statistic"] == 1.0

    # 2. Data with missing values (np.nan)
    missing_data = np.array([
        [0.0, 1.0, 2.0, np.nan],
        [0.0, 1.0, 2.0, 1.0],
        [np.nan, 1.0, 2.0, 1.0]
    ])
    res_missing = AgreementMetrics.krippendorff_alpha(missing_data, level="ordinal")
    assert res_missing["status"] == "COMPUTED"
    assert res_missing["statistic"] == 1.0  # Perfect agreement on all available pairs

    # 3. Disagreement data
    disagree_data = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 2.0, 2.0]
    ])
    res_disagree = AgreementMetrics.krippendorff_alpha(disagree_data, level="ordinal")
    assert res_disagree["status"] == "COMPUTED"
    assert res_disagree["statistic"] < 0.0  # Systematic disagreement yields negative alpha


def test_cohens_kappa_bootstrap_ci():
    """Verify Cohen's kappa computes bootstrap confidence intervals."""
    y1 = [ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW, ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM] * 4
    y2 = [ExpertLabelClass.HIGH, ExpertLabelClass.MEDIUM, ExpertLabelClass.LOW, ExpertLabelClass.HIGH, ExpertLabelClass.LOW] * 4

    res = AgreementMetrics.cohens_kappa(y1, y2, weights="quadratic", bootstrap_ci=True, n_bootstraps=500)
    assert res["status"] == "COMPUTED"
    assert res["statistic"] > 0.8
    assert res["bootstrap_ci_95"] is not None
    assert len(res["bootstrap_ci_95"]) == 2
    assert res["bootstrap_ci_95"][0] <= res["statistic"] <= res["bootstrap_ci_95"][1]


def test_per_class_agreement_and_confusion_matrix():
    """Verify per-class F1 and confusion matrix calculation."""
    y1 = [ExpertLabelClass.LOW, ExpertLabelClass.LOW, ExpertLabelClass.MEDIUM, ExpertLabelClass.HIGH]
    y2 = [ExpertLabelClass.LOW, ExpertLabelClass.MEDIUM, ExpertLabelClass.MEDIUM, ExpertLabelClass.HIGH]

    res = AgreementMetrics.per_class_agreement(y1, y2)
    assert res["status"] == "COMPUTED"
    assert "confusion_matrix" in res
    assert res["classes"] == ["LOW", "MEDIUM", "HIGH"]
    assert res["per_class_f1"]["HIGH"] == 1.0  # Perfect agreement on HIGH
    assert res["overall_accuracy"] == 0.75  # 3 of 4 match
