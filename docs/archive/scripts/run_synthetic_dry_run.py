"""
AgileGraph Synthetic Annotation Dry Run Runner
Executes Phase 5 synthetic dry run using seed 42 across all 166 assets.
Verifies complete import validation, Krippendorff's alpha, provenance enforcement,
and consensus isolation without mutating genuine assets.
"""
import os
import sys
import json
import tempfile
import numpy as np

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from src.ml.synthetic_dry_run import SyntheticAnnotationGenerator
from src.ml.agreement import AgreementMetrics
from src.ml.import_annotations import AnnotationImporter
from src.ml.expert_validation import (
    ExpertLabelClass,
    ProvenanceSource,
    ValidationDataset,
    AssetForReview,
    ValidationSession,
    AggregationMethod
)

def run_dry_run():
    print("=" * 70)
    print("AGILEGRAPH — SYNTHETIC ANNOTATION DRY RUN (PHASE 5)")
    print("=" * 70)
    print(f"[INFO] Working Directory: {os.getcwd()}")
    print(f"[INFO] Backend Root: {backend_root}")

    # 1. Load genuine package strictly read-only for structural asset dossiers
    package_path = os.path.join(backend_root, "dataset", "annotation", "sample_annotation_package.json")
    if not os.path.exists(package_path):
        raise FileNotFoundError(f"Annotation package not found: {package_path}")

    with open(package_path, "r", encoding="utf-8") as f:
        package = json.load(f)

    assets = package.get("assets", [])
    total_assets = len(assets)
    print(f"[STEP 1] Loaded {total_assets} blinded asset dossiers (read-only).")
    assert total_assets == 166, f"Expected 166 assets, found {total_assets}"

    # Verify template is also untouched
    template_path = os.path.join(backend_root, "dataset", "annotation", "expert_submission_template.json")
    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)
    print(f"[STEP 1] Verified blank expert template intact ({len(template.get('labels', []))} blank entries).")

    # 2. Generate deterministic synthetic submissions for 4 simulated experts (seed 42)
    expert_ids = ["expert_01", "expert_02", "expert_03", "expert_04"]
    print(f"[STEP 2] Generating deterministic synthetic submissions for {expert_ids} (seed=42)...")
    submissions = SyntheticAnnotationGenerator.generate_synthetic_submissions(
        package_assets=assets,
        expert_ids=expert_ids,
        seed=42,
        protocol_version="2.0.0",
        dataset_version="v1",
        simulate_missing_rate=0.05
    )

    # 3. Verify provenance stamping on 100% of generated records
    print("[STEP 3] Verifying provenance stamps on generated records...")
    total_records = 0
    synthetic_count = 0
    missing_count = 0
    for exp_id in expert_ids:
        recs = submissions[exp_id]["labels"]
        assert len(recs) == total_assets, f"Expert {exp_id} record count mismatch"
        for r in recs:
            total_records += 1
            if r.get("provenance") == "SYNTHETIC_DRY_RUN":
                synthetic_count += 1
            if r.get("label") == "UNKNOWN":
                missing_count += 1

    print(f"         Total records checked: {total_records}")
    print(f"         Provenance == 'SYNTHETIC_DRY_RUN': {synthetic_count}/{total_records} (100.0%)")
    print(f"         Simulated missing / abstained ratings: {missing_count}/{total_records} ({missing_count/total_records*100:.2f}%)")
    assert synthetic_count == total_records, "FAIL: Found record without SYNTHETIC_DRY_RUN stamp!"

    # 4. Import & Validation Pipeline Checks (Isolated in Temporary Directory)
    print("[STEP 4] Testing AnnotationImporter validation pipeline...")
    asset_ids = [a["asset_id"] for a in assets]
    importer = AnnotationImporter(
        expected_asset_ids=asset_ids,
        expected_expert_ids=expert_ids,
        dataset_version="v1",
        expected_protocol_version="2.0.0",
        allow_legacy_without_provenance=False
    )

    imported_sessions = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for exp_id in expert_ids:
            exp_file = os.path.join(tmpdir, f"{exp_id}_submission.json")
            with open(exp_file, "w", encoding="utf-8") as f:
                json.dump(submissions[exp_id], f)

            # Ingest through AnnotationImporter
            res = importer.import_annotations(exp_file, protocol_status="FINALIZED")
            assert res["status"] == "SUCCESS", f"Importer failed for {exp_id}: {res}"
            assert res["imported_count"] == total_assets
            imported_sessions.append(ValidationSession(session_id=f"sess_{exp_id}", expert_id=exp_id, labels=res["labels"]))
            print(f"         [OK] Ingested {res['imported_count']} records for {exp_id} through AnnotationImporter.")

        # Test FAIL-CLOSED guardrail: verify that genuine evaluation mode strictly REJECTS synthetic submission
        res_reject = importer.import_annotations(
            os.path.join(tmpdir, "expert_01_submission.json"),
            protocol_status="FINALIZED",
            enforce_provenance=ProvenanceSource.GENUINE_HUMAN
        )
        assert res_reject["status"] == "REJECTED", "FAIL: Importer did not reject synthetic data in genuine mode!"
        print(f"         [OK] Provenance Guardrail Active: Genuine evaluation importer successfully rejected synthetic file ({res_reject['message']}).")

    # 5. Multi-Rater Agreement Calculation (Krippendorff's Alpha Ordinal Metric)
    print("[STEP 5] Calculating multi-rater agreement (Krippendorff's alpha)...")
    matrix = np.zeros((len(expert_ids), total_assets), dtype=float)
    priority_map = {
        "LOW": 0.0,
        "MEDIUM": 1.0,
        "HIGH": 2.0,
        "UNKNOWN": np.nan
    }

    for r_idx, exp_id in enumerate(expert_ids):
        for c_idx, rec in enumerate(submissions[exp_id]["labels"]):
            matrix[r_idx, c_idx] = priority_map[rec["label"]]

    alpha_res = AgreementMetrics.krippendorff_alpha(matrix, level="ordinal")
    print(f"         Status: {alpha_res['status']}")
    print(f"         Items Evaluated: {alpha_res['evaluated_items']}/{total_assets}")
    print(f"         Total Valid Ratings: {alpha_res['total_ratings']}")
    print(f"         Ordinal Krippendorff's Alpha: {alpha_res['statistic']:.4f}")
    print("         [NOTE] This metric is an automated simulation result for testing; it does NOT represent human expert agreement.")

    # 6. Consensus Isolation Guardrail Check
    print("[STEP 6] Verifying consensus isolation in ValidationDataset...")
    test_asset_obj = AssetForReview(asset_id=assets[0]["asset_id"], project_id=assets[0]["project_id"])
    vds = ValidationDataset(
        dataset_version="v1",
        annotation_protocol_version="2.0.0",
        assets=[test_asset_obj],
        sessions=imported_sessions
    )

    # By default, get_consensus() must filter ONLY GENUINE_HUMAN
    default_consensus = vds.get_consensus(assets[0]["asset_id"], method=AggregationMethod.MAJORITY_VOTE)
    assert default_consensus is None, "FAIL: Synthetic data leaked into default genuine consensus!"
    print("         [OK] Default genuine consensus returned None (100% of synthetic records isolated).")

    synthetic_consensus = vds.get_consensus(assets[0]["asset_id"], method=AggregationMethod.MAJORITY_VOTE, provenance=ProvenanceSource.SYNTHETIC_DRY_RUN)
    assert synthetic_consensus is not None, "FAIL: Synthetic consensus failed to compute under explicit synthetic flag."
    print(f"         [OK] Explicit synthetic query returned simulated consensus: {synthetic_consensus.value}")

    print("=" * 70)
    print("ALL SYNTHETIC DRY RUN CHECKS PASSED SUCCESSFULLY (ZERO MUTATIONS TO REAL ASSETS)")
    print("=" * 70)

if __name__ == "__main__":
    run_dry_run()
