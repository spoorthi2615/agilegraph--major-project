import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
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
    ProvenanceSource,
)


class AnnotationImporter:
    def __init__(
        self,
        expected_asset_ids: List[str],
        expected_expert_ids: List[str],
        dataset_version: str,
        expected_protocol_version: str = "2.0.0",
        allow_legacy_without_provenance: bool = False,
    ):
        self.expected_asset_ids = set(expected_asset_ids)
        self.expected_expert_ids = set(expected_expert_ids)
        self.dataset_version = dataset_version
        self.expected_protocol_version = expected_protocol_version
        self.allow_legacy_without_provenance = allow_legacy_without_provenance

    def import_annotations(
        self,
        filepath: str,
        protocol_status: str,
        enforce_provenance: Optional[ProvenanceSource] = None,
    ) -> Dict[str, Any]:
        """
        Imports expert annotations strictly validating constraints.
        Enforces protocol finalization, asset ID consistency, expert pseudonyms,
        valid enum ranges, non-empty timestamps, and prevents duplicate ratings.
        Enforces FAIL-CLOSED provenance validation: records with missing or invalid provenance
        are rejected unless allow_legacy_without_provenance is explicitly enabled.
        If enforce_provenance is provided (e.g. ProvenanceSource.GENUINE_HUMAN),
        any record with a differing provenance will be strictly rejected.
        """
        if protocol_status != "FINALIZED":
            return {
                "status": "REJECTED",
                "message": f"Cannot import annotations while protocol is {protocol_status}."
            }

        if not os.path.exists(filepath):
            return {
                "status": "REJECTED",
                "message": "File not found."
            }

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return {"status": "REJECTED", "message": "Invalid JSON format."}

        imported_labels: List[ExpertLabel] = []
        imported_adjudications: List[AdjudicatedLabel] = []
        seen = set()

        valid_label_values = {e.value for e in ExpertLabelClass}
        valid_crypto_values = {e.value for e in CryptoConcern}
        valid_data_values = {e.value for e in SensitiveDataImpact}
        valid_exposure_values = {e.value for e in ExposureLevel}
        valid_pq_values = {e.value for e in PostQuantumUrgency}
        valid_conf_values = {e.value for e in EvidenceConfidence}
        valid_status_values = {e.value for e in AnnotationStatus}
        valid_provenance_values = {e.value for e in ProvenanceSource}

        # 1. Validate primary expert labels
        for record in data.get("labels", []):
            asset_id = record.get("asset_id")
            expert_id = record.get("expert_id") or record.get("annotator_id")
            label_val = record.get("label") or record.get("migration_priority")
            ts = record.get("timestamp")
            dv = record.get("dataset_version")
            proto_v = record.get("annotation_protocol_version")
            raw_provenance = record.get("provenance")

            if not asset_id or asset_id not in self.expected_asset_ids:
                return {"status": "REJECTED", "message": f"Unknown asset ID: {asset_id}"}

            if not expert_id or expert_id not in self.expected_expert_ids:
                return {"status": "REJECTED", "message": f"Unknown expert ID: {expert_id}"}

            if not label_val or label_val not in valid_label_values:
                return {"status": "REJECTED", "message": f"Invalid label: {label_val}"}

            if not ts:
                return {"status": "REJECTED", "message": "Malformed timestamp."}

            if dv != self.dataset_version:
                return {"status": "REJECTED", "message": "Inconsistent dataset version."}

            if proto_v and proto_v != self.expected_protocol_version and proto_v != "v1":
                return {"status": "REJECTED", "message": f"Inconsistent protocol version: {proto_v}"}

            # Fail-closed provenance check
            if raw_provenance is None:
                if not self.allow_legacy_without_provenance:
                    return {
                        "status": "REJECTED",
                        "message": "Missing provenance metadata. Explicit provenance is required to prevent synthetic data leakage."
                    }
                resolved_provenance = ProvenanceSource.GENUINE_HUMAN
            else:
                if raw_provenance not in valid_provenance_values:
                    return {
                        "status": "REJECTED",
                        "message": f"Invalid provenance metadata: {raw_provenance}. Must be one of {valid_provenance_values}."
                    }
                resolved_provenance = ProvenanceSource(raw_provenance)

            # Strict provenance constraint if requested
            if enforce_provenance is not None and resolved_provenance != enforce_provenance:
                return {
                    "status": "REJECTED",
                    "message": f"Provenance mismatch: Expected {enforce_provenance.value}, got {resolved_provenance.value}."
                }

            # Optional multi-dimensional rubric attributes
            cc = record.get("crypto_concern")
            if cc and cc not in valid_crypto_values:
                return {"status": "REJECTED", "message": f"Invalid crypto_concern: {cc}"}

            sdi = record.get("sensitive_data_impact")
            if sdi and sdi not in valid_data_values:
                return {"status": "REJECTED", "message": f"Invalid sensitive_data_impact: {sdi}"}

            exp = record.get("exposure")
            if exp and exp not in valid_exposure_values:
                return {"status": "REJECTED", "message": f"Invalid exposure: {exp}"}

            pqu = record.get("post_quantum_urgency")
            if pqu and pqu not in valid_pq_values:
                return {"status": "REJECTED", "message": f"Invalid post_quantum_urgency: {pqu}"}

            conf = record.get("evidence_confidence")
            if conf and conf not in valid_conf_values:
                return {"status": "REJECTED", "message": f"Invalid evidence_confidence: {conf}"}

            stat = record.get("status")
            if stat and stat not in valid_status_values:
                return {"status": "REJECTED", "message": f"Invalid status: {stat}"}

            pair = (asset_id, expert_id)
            if pair in seen:
                return {"status": "REJECTED", "message": "Duplicate rating for same asset by same expert."}
            seen.add(pair)

            imported_labels.append(ExpertLabel(
                asset_id=asset_id,
                project_id=record.get("project_id", asset_id.split(":")[0] if ":" in asset_id else "unknown"),
                expert_id=expert_id,
                commit_sha=record.get("commit_sha"),
                label=ExpertLabelClass(label_val),
                crypto_concern=CryptoConcern(cc) if cc else CryptoConcern.UNKNOWN_OR_UNCLASSIFIED,
                sensitive_data_impact=SensitiveDataImpact(sdi) if sdi else SensitiveDataImpact.UNKNOWN_OR_INSUFFICIENT_EVIDENCE,
                exposure=ExposureLevel(exp) if exp else ExposureLevel.UNKNOWN,
                post_quantum_urgency=PostQuantumUrgency(pqu) if pqu else PostQuantumUrgency.INVESTIGATE_FURTHER,
                evidence_confidence=EvidenceConfidence(conf) if conf else EvidenceConfidence.MEDIUM,
                rationale=record.get("rationale", ""),
                status=AnnotationStatus(stat) if stat else AnnotationStatus.SUBMITTED,
                rubric_version=record.get("rubric_version", self.expected_protocol_version),
                timestamp=ts,
                dataset_version=dv,
                annotation_protocol_version=proto_v or self.expected_protocol_version,
                provenance=resolved_provenance
            ))

        # 2. Validate adjudicated labels if present
        for adj_record in data.get("adjudicated_labels", []):
            aid = adj_record.get("asset_id")
            adj_id = adj_record.get("adjudicator_id")
            adj_prio = adj_record.get("adjudicated_priority")

            if not aid or aid not in self.expected_asset_ids:
                return {"status": "REJECTED", "message": f"Unknown asset ID in adjudication: {aid}"}

            if not adj_id:
                return {"status": "REJECTED", "message": "Missing adjudicator ID."}

            if not adj_prio or adj_prio not in valid_label_values:
                return {"status": "REJECTED", "message": f"Invalid adjudicated priority: {adj_prio}"}

            imported_adjudications.append(AdjudicatedLabel(
                asset_id=aid,
                project_id=adj_record.get("project_id", aid.split(":")[0] if ":" in aid else "unknown"),
                commit_sha=adj_record.get("commit_sha"),
                adjudicated_priority=ExpertLabelClass(adj_prio),
                adjudicator_id=adj_id,
                adjudication_rationale=adj_record.get("adjudication_rationale", ""),
                adjudication_method=AggregationMethod(adj_record.get("adjudication_method", "ADJUDICATION")),
                timestamp=adj_record.get("timestamp", datetime.now(timezone.utc).isoformat())
            ))

        return {
            "status": "SUCCESS",
            "imported_count": len(imported_labels),
            "adjudicated_count": len(imported_adjudications),
            "labels": imported_labels,
            "adjudications": imported_adjudications
        }
