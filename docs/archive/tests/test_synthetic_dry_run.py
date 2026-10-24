import pytest
import os
import json
import tempfile
import numpy as np

from src.ml.expert_validation import (
    ExpertLabelClass,
    ProvenanceSource,
    AggregationMethod,
    ValidationDataset,
    AssetForReview,
    ValidationSession,
)
from src.ml.import_annotations import AnnotationImporter
from src.ml.synthetic_dry_run import SyntheticAnnotationGenerator
from src.ml.agreement import AgreementMetrics


@pytest.fixture
def sample_dossiers():
    return [
        {
            "asset_id": "test_repo:crypto/rsa.py",
            "project_id": "test_repo",
            "commit_sha": "abc1234",
            "language": "python",
        },
        {
            "asset_id": "test_repo:crypto/aes.py",
            "project_id": "test_repo",
            "commit_sha": "abc1234",
            "language": "python",
        },
        {
            "asset_id": "test_repo:jwt/signer.py",
            "project_id": "test_repo",
            "commit_sha": "abc1234",
            "language": "python",
        },
    ]


def test_synthetic_generation_provenance_stamping(sample_dossiers):
    submissions = SyntheticAnnotationGenerator.generate_synthetic_submissions(
        package_assets=sample_dossiers,
        expert_ids=["expert_01", "expert_02"],
        seed=123,
    )

    assert "expert_01" in submissions
    assert "expert_02" in submissions
    assert len(submissions["expert_01"]["labels"]) == 3

    for record in submissions["expert_01"]["labels"]:
        # Provenance must be explicitly stamped as SYNTHETIC_DRY_RUN
        assert record["provenance"] == "SYNTHETIC_DRY_RUN"
        assert "SYNTHETIC DRY RUN" in record["rationale"]


def test_synthetic_importer_provenance_propagation(sample_dossiers):
    submissions = SyntheticAnnotationGenerator.generate_synthetic_submissions(
        package_assets=sample_dossiers,
        expert_ids=["expert_01"],
        seed=42,
    )

    asset_ids = [a["asset_id"] for a in sample_dossiers]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=["expert_01"],
        dataset_version="v1",
        expected_protocol_version="2.0.0",
    )

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(submissions["expert_01"], f)
        temp_path = f.name

    try:
        res = importer.import_annotations(temp_path, protocol_status="FINALIZED")
        assert res["status"] == "SUCCESS"
        assert res["imported_count"] == 3
        for label in res["labels"]:
            # Model must preserve provenance
            assert label.provenance == ProvenanceSource.SYNTHETIC_DRY_RUN
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_provenance_isolation_guardrail(sample_dossiers):
    submissions = SyntheticAnnotationGenerator.generate_synthetic_submissions(
        package_assets=sample_dossiers,
        expert_ids=["expert_01"],
        seed=42,
    )

    # Convert to ExpertLabel objects
    from src.ml.expert_validation import ExpertLabel
    labels = [ExpertLabel(**rec) for rec in submissions["expert_01"]["labels"]]

    # Verify that genuine filter excludes synthetic records completely
    genuine_only = [l for l in labels if l.provenance == ProvenanceSource.GENUINE_HUMAN]
    assert len(genuine_only) == 0

    synthetic_only = [l for l in labels if l.provenance == ProvenanceSource.SYNTHETIC_DRY_RUN]
    assert len(synthetic_only) == 3


def test_synthetic_dry_run_multi_rater_agreement(sample_dossiers):
    # Generate 4 rater submissions
    experts = ["expert_01", "expert_02", "expert_03", "expert_04"]
    submissions = SyntheticAnnotationGenerator.generate_synthetic_submissions(
        package_assets=sample_dossiers,
        expert_ids=experts,
        seed=999,
        simulate_missing_rate=0.0,
    )

    # Encode reliability matrix for Krippendorff's alpha
    n_items = len(sample_dossiers)
    m_raters = len(experts)
    matrix = np.zeros((m_raters, n_items), dtype=float)

    priority_map = {
        ExpertLabelClass.LOW.value: 0.0,
        ExpertLabelClass.MEDIUM.value: 1.0,
        ExpertLabelClass.HIGH.value: 2.0,
        ExpertLabelClass.UNKNOWN.value: np.nan,
    }

    for r_idx, exp_id in enumerate(experts):
        for c_idx, rec in enumerate(submissions[exp_id]["labels"]):
            matrix[r_idx, c_idx] = priority_map[rec["label"]]

    alpha_res = AgreementMetrics.krippendorff_alpha(matrix, level="ordinal")
    assert alpha_res["status"] == "COMPUTED"
    assert "statistic" in alpha_res
    assert alpha_res["evaluated_items"] == 3


def test_importer_rejects_missing_provenance_by_default(sample_dossiers):
    """Fail-closed: Submissions without explicit provenance must be rejected."""
    asset_ids = [a["asset_id"] for a in sample_dossiers]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=["expert_01"],
        dataset_version="v1",
        expected_protocol_version="2.0.0",
        allow_legacy_without_provenance=False
    )

    payload = {
        "labels": [{
            "asset_id": sample_dossiers[0]["asset_id"],
            "expert_id": "expert_01",
            "label": "HIGH",
            "timestamp": "2026-10-12T00:00:00Z",
            "dataset_version": "v1"
            # provenance key deliberately missing!
        }]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        temp_path = f.name

    try:
        res = importer.import_annotations(temp_path, protocol_status="FINALIZED")
        assert res["status"] == "REJECTED"
        assert "Missing provenance metadata" in res["message"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_importer_accepts_missing_provenance_with_legacy_flag(sample_dossiers):
    """Explicit legacy flag enables migration for trusted legacy files."""
    asset_ids = [a["asset_id"] for a in sample_dossiers]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=["expert_01"],
        dataset_version="v1",
        expected_protocol_version="2.0.0",
        allow_legacy_without_provenance=True  # Trusted legacy mode
    )

    payload = {
        "labels": [{
            "asset_id": sample_dossiers[0]["asset_id"],
            "expert_id": "expert_01",
            "label": "HIGH",
            "timestamp": "2026-10-12T00:00:00Z",
            "dataset_version": "v1"
        }]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        temp_path = f.name

    try:
        res = importer.import_annotations(temp_path, protocol_status="FINALIZED")
        assert res["status"] == "SUCCESS"
        assert res["imported_count"] == 1
        assert res["labels"][0].provenance == ProvenanceSource.GENUINE_HUMAN
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_importer_rejects_invalid_provenance(sample_dossiers):
    """Submissions with unknown provenance string must be rejected."""
    asset_ids = [a["asset_id"] for a in sample_dossiers]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=["expert_01"],
        dataset_version="v1",
        expected_protocol_version="2.0.0"
    )

    payload = {
        "labels": [{
            "asset_id": sample_dossiers[0]["asset_id"],
            "expert_id": "expert_01",
            "label": "HIGH",
            "timestamp": "2026-10-12T00:00:00Z",
            "dataset_version": "v1",
            "provenance": "FABRICATED_UNVERIFIED_DATA"
        }]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        temp_path = f.name

    try:
        res = importer.import_annotations(temp_path, protocol_status="FINALIZED")
        assert res["status"] == "REJECTED"
        assert "Invalid provenance metadata" in res["message"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_importer_enforce_provenance_rejects_synthetic(sample_dossiers):
    """When importing for genuine research evaluation, synthetic records are strictly rejected."""
    asset_ids = [a["asset_id"] for a in sample_dossiers]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=["expert_01"],
        dataset_version="v1",
        expected_protocol_version="2.0.0"
    )

    payload = {
        "labels": [{
            "asset_id": sample_dossiers[0]["asset_id"],
            "expert_id": "expert_01",
            "label": "HIGH",
            "timestamp": "2026-10-12T00:00:00Z",
            "dataset_version": "v1",
            "provenance": "SYNTHETIC_DRY_RUN"
        }]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        temp_path = f.name

    try:
        res = importer.import_annotations(
            temp_path,
            protocol_status="FINALIZED",
            enforce_provenance=ProvenanceSource.GENUINE_HUMAN
        )
        assert res["status"] == "REJECTED"
        assert "Provenance mismatch" in res["message"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_validation_dataset_consensus_isolates_synthetic(sample_dossiers):
    """ValidationDataset.get_consensus ignores synthetic labels by default."""
    from src.ml.expert_validation import ExpertLabel

    aid = sample_dossiers[0]["asset_id"]

    # Session 1: Real expert voted LOW
    l_genuine = ExpertLabel(
        asset_id=aid,
        project_id="test_repo",
        expert_id="expert_01",
        label=ExpertLabelClass.LOW,
        timestamp="2026-10-12T00:00:00Z",
        provenance=ProvenanceSource.GENUINE_HUMAN
    )

    # Session 2: Synthetic rater voted HIGH
    l_synthetic = ExpertLabel(
        asset_id=aid,
        project_id="test_repo",
        expert_id="expert_02",
        label=ExpertLabelClass.HIGH,
        timestamp="2026-10-12T00:00:00Z",
        provenance=ProvenanceSource.SYNTHETIC_DRY_RUN
    )

    vds = ValidationDataset(
        dataset_version="v1",
        annotation_protocol_version="2.0.0",
        assets=[AssetForReview(asset_id=aid, project_id="test_repo")],
        sessions=[
            ValidationSession(session_id="s1", expert_id="expert_01", labels=[l_genuine]),
            ValidationSession(session_id="s2", expert_id="expert_02", labels=[l_synthetic]),
        ]
    )

    # By default, consensus considers ONLY GENUINE_HUMAN labels
    consensus_default = vds.get_consensus(aid, method=AggregationMethod.MAJORITY_VOTE)
    assert consensus_default == ExpertLabelClass.LOW  # Not swayed by synthetic vote!

    # Explicit synthetic query
    consensus_synthetic = vds.get_consensus(aid, method=AggregationMethod.MAJORITY_VOTE, provenance=ProvenanceSource.SYNTHETIC_DRY_RUN)
    assert consensus_synthetic == ExpertLabelClass.HIGH
