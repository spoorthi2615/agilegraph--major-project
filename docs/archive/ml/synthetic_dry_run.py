import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from src.ml.expert_validation import (
    ExpertLabelClass,
    CryptoConcern,
    SensitiveDataImpact,
    ExposureLevel,
    PostQuantumUrgency,
    EvidenceConfidence,
    AnnotationStatus,
    ProvenanceSource,
)


class SyntheticAnnotationGenerator:
    """
    Generates deterministic, isolated synthetic annotation submissions for smoke testing
    and validation pipeline verification during expert recruitment periods.
    
    SAFETY MANDATES:
    - All generated records are strictly stamped with provenance = "SYNTHETIC_DRY_RUN".
    - Outputs are never stored in real expert paths.
    - Deterministic random seed ensures reproducible dry-run outcomes.
    - Does NOT represent empirical evidence or ground truth.
    """

    DEFAULT_EXPERTS = ["expert_01", "expert_02", "expert_03", "expert_04"]

    @staticmethod
    def generate_synthetic_submissions(
        package_assets: List[Dict[str, Any]],
        expert_ids: Optional[List[str]] = None,
        seed: int = 42,
        protocol_version: str = "2.0.0",
        dataset_version: str = "v1",
        simulate_missing_rate: float = 0.05,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generates simulated submissions for each expert across the given asset dossiers.
        Returns a dictionary mapping expert_id to their submission payload.
        """
        rng = random.Random(seed)
        experts = expert_ids or SyntheticAnnotationGenerator.DEFAULT_EXPERTS

        # Priority distribution (ordinal classes)
        priority_choices = [
            ExpertLabelClass.HIGH,
            ExpertLabelClass.MEDIUM,
            ExpertLabelClass.LOW,
        ]

        expert_submissions = {exp_id: {"labels": []} for exp_id in experts}

        for asset in package_assets:
            aid = asset.get("asset_id")
            pid = asset.get("project_id", aid.split(":")[0] if ":" in aid else "unknown")
            commit_sha = asset.get("commit_sha")

            # Create a latent base priority for this asset so annotators have realistic partial agreement
            latent_priority = rng.choice(priority_choices)

            for exp_id in experts:
                # Decide if this rating is missing / abstained
                if rng.random() < simulate_missing_rate:
                    chosen_priority = ExpertLabelClass.UNKNOWN
                    rationale = "SYNTHETIC DRY RUN: Abstention / insufficient observable evidence"
                else:
                    # 80% chance of agreeing with latent ground, 20% adjacent deviation
                    r = rng.random()
                    if r < 0.80:
                        chosen_priority = latent_priority
                    else:
                        chosen_priority = rng.choice(priority_choices)
                    rationale = f"SYNTHETIC DRY RUN: Simulated automated test rating for {aid}"

                record = {
                    "asset_id": aid,
                    "project_id": pid,
                    "expert_id": exp_id,
                    "annotator_id": exp_id,
                    "commit_sha": commit_sha,
                    "label": chosen_priority.value,
                    "migration_priority": chosen_priority.value,
                    "crypto_concern": CryptoConcern.CLASSICAL_VULNERABLE_PQC.value if chosen_priority == ExpertLabelClass.HIGH else CryptoConcern.POST_QUANTUM_READY.value,
                    "sensitive_data_impact": SensitiveDataImpact.CREDENTIALS_OR_SECRETS.value if chosen_priority == ExpertLabelClass.HIGH else SensitiveDataImpact.INTERNAL_OR_ANCILLARY.value,
                    "exposure": ExposureLevel.INTERNET_FACING.value if chosen_priority == ExpertLabelClass.HIGH else ExposureLevel.INTERNAL.value,
                    "post_quantum_urgency": PostQuantumUrgency.IMMEDIATE_ACTION.value if chosen_priority == ExpertLabelClass.HIGH else PostQuantumUrgency.MONITOR.value,
                    "evidence_confidence": EvidenceConfidence.HIGH.value,
                    "rationale": rationale,
                    "status": AnnotationStatus.SUBMITTED.value,
                    "rubric_version": protocol_version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "dataset_version": dataset_version,
                    "annotation_protocol_version": protocol_version,
                    # MANDATORY PROVENANCE STAMP
                    "provenance": ProvenanceSource.SYNTHETIC_DRY_RUN.value,
                }
                expert_submissions[exp_id]["labels"].append(record)

        return expert_submissions
