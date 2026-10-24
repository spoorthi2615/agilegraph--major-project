from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, model_validator
import datetime


class ExpertLabelClass(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"  # Represents abstention / cannot assess


class CryptoConcern(str, Enum):
    CLASSICAL_BROKEN = "CLASSICAL_BROKEN"  # MD5, SHA1, DES, 3DES, RC4
    CLASSICAL_VULNERABLE_PQC = "CLASSICAL_VULNERABLE_PQC"  # RSA, ECC, ECDSA, DH, DSA (vulnerable to Shor's algorithm)
    QUANTUM_VULNERABLE_STRONG = "QUANTUM_VULNERABLE_STRONG"  # Symmetric key < 256 bits (Grover's reduction)
    POST_QUANTUM_READY = "POST_QUANTUM_READY"  # NIST PQC (ML-KEM, ML-DSA, SLH-DSA, Kyber, Dilithium, AES-256)
    UNKNOWN_OR_UNCLASSIFIED = "UNKNOWN_OR_UNCLASSIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SensitiveDataImpact(str, Enum):
    CREDENTIALS_OR_SECRETS = "CREDENTIALS_OR_SECRETS"  # Passwords, private keys, API secrets, authentication tokens
    PERSONAL_DATA_PII = "PERSONAL_DATA_PII"  # Personal identifiable data, identity records, financial/health
    COMMUNICATION_CONTENT = "COMMUNICATION_CONTENT"  # In-transit payloads, encrypted sessions, messages
    INTEGRITY_TOKEN = "INTEGRITY_TOKEN"  # Checksums, message authentication codes, anti-tamper tokens
    INTERNAL_OR_ANCILLARY = "INTERNAL_OR_ANCILLARY"  # Internal system identifiers, telemetry, cache tokens
    UNKNOWN_OR_INSUFFICIENT_EVIDENCE = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"


class ExposureLevel(str, Enum):
    INTERNET_FACING = "INTERNET_FACING"  # Directly exposed to untrusted external networks
    INTERNAL = "INTERNAL"  # Restrictive intranet or local boundary
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Library routine or standalone utility with no network surface
    UNKNOWN = "UNKNOWN"  # Exposure cannot be conclusively established


class PostQuantumUrgency(str, Enum):
    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"  # Asymmetric key exchange / signing with long shelf-life (SNDL risk)
    PLANNED_MIGRATION = "PLANNED_MIGRATION"  # Standard classical asymmetric requiring roadmap transition
    MONITOR = "MONITOR"  # Quantum-resistant symmetric (e.g. AES-256, SHA-384/512)
    INVESTIGATE_FURTHER = "INVESTIGATE_FURTHER"  # Insufficient or conflicting code evidence


class EvidenceConfidence(str, Enum):
    HIGH = "HIGH"  # Unambiguous cryptographic call site, clear parameter or certificate
    MEDIUM = "MEDIUM"  # High-level crypto wrapper or inferred usage with partial context
    LOW = "LOW"  # Weak indirect cues, wrapper naming, or ambiguous imports


class AnnotationStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ADJUDICATED = "ADJUDICATED"
    DRAFT = "DRAFT"


class Expert(BaseModel):
    expert_id: str  # Pseudonymous identifier (e.g. expert_01)
    # No PII stored here to respect privacy model


class AssetForReview(BaseModel):
    asset_id: str
    project_id: str
    commit_sha: Optional[str] = None
    language: Optional[str] = None
    relative_path: Optional[str] = None
    heuristic_score: Optional[float] = None  # Used ONLY as a post-hoc evaluation comparator; NEVER revealed to annotator
    scanner_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    factor_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProvenanceSource(str, Enum):
    GENUINE_HUMAN = "GENUINE_HUMAN"
    SYNTHETIC_DRY_RUN = "SYNTHETIC_DRY_RUN"


class ExpertLabel(BaseModel):
    asset_id: str
    project_id: str
    expert_id: str
    label: ExpertLabelClass = ExpertLabelClass.UNKNOWN  # Primary migration priority
    commit_sha: Optional[str] = None
    annotator_id: Optional[str] = None

    # Multi-dimensional rubric assessments
    crypto_concern: CryptoConcern = CryptoConcern.UNKNOWN_OR_UNCLASSIFIED
    sensitive_data_impact: SensitiveDataImpact = SensitiveDataImpact.UNKNOWN_OR_INSUFFICIENT_EVIDENCE
    exposure: ExposureLevel = ExposureLevel.UNKNOWN
    post_quantum_urgency: PostQuantumUrgency = PostQuantumUrgency.INVESTIGATE_FURTHER
    evidence_confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM
    rationale: str = ""

    status: AnnotationStatus = AnnotationStatus.SUBMITTED
    rubric_version: str = "2.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    dataset_version: str = "v1"
    annotation_protocol_version: str = "2.0.0"
    provenance: ProvenanceSource = ProvenanceSource.GENUINE_HUMAN

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If annotator_id is passed instead of expert_id
            if "annotator_id" in data and "expert_id" not in data:
                data["expert_id"] = data["annotator_id"]
            elif "expert_id" in data and "annotator_id" not in data:
                data["annotator_id"] = data["expert_id"]

            # If migration_priority is passed instead of label
            if "migration_priority" in data and "label" not in data:
                data["label"] = data["migration_priority"]
        return data


class AggregationMethod(str, Enum):
    MAJORITY_VOTE = "MAJORITY_VOTE"
    ADJUDICATION = "ADJUDICATION"
    EXPERT_CONSENSUS = "EXPERT_CONSENSUS"


class AdjudicatedLabel(BaseModel):
    asset_id: str
    project_id: str
    commit_sha: Optional[str] = None
    adjudicated_priority: ExpertLabelClass
    adjudicator_id: str  # e.g. "expert_lead" or "consensus_board"
    original_expert_labels: List[ExpertLabel] = Field(default_factory=list)
    adjudication_rationale: str = ""
    adjudication_method: AggregationMethod = AggregationMethod.ADJUDICATION
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class ValidationSession(BaseModel):
    session_id: str
    expert_id: str
    labels: List[ExpertLabel]


class ValidationDataset(BaseModel):
    dataset_version: str
    annotation_protocol_version: str
    assets: List[AssetForReview]
    sessions: List[ValidationSession]
    adjudicated_labels: List[AdjudicatedLabel] = Field(default_factory=list)

    def get_labels_for_asset(
        self,
        asset_id: str,
        provenance: Optional[ProvenanceSource] = ProvenanceSource.GENUINE_HUMAN
    ) -> List[ExpertLabel]:
        """
        Retrieves expert labels for an asset. By default, strictly returns GENUINE_HUMAN labels.
        Pass provenance=None to retrieve all labels, or ProvenanceSource.SYNTHETIC_DRY_RUN for simulated data.
        """
        labels = []
        for s in self.sessions:
            for l in s.labels:
                if l.asset_id == asset_id:
                    if provenance is None or l.provenance == provenance:
                        labels.append(l)
        return labels

    def get_consensus(
        self,
        asset_id: str,
        method: AggregationMethod,
        provenance: Optional[ProvenanceSource] = ProvenanceSource.GENUINE_HUMAN
    ) -> Optional[ExpertLabelClass]:
        """
        Computes consensus migration priority for an asset.
        Defaults strictly to GENUINE_HUMAN provenance, preventing synthetic ratings
        from ever influencing genuine research consensus labels.
        """
        # Check adjudicated first if adjudication method
        if method == AggregationMethod.ADJUDICATION:
            for adj in self.adjudicated_labels:
                if adj.asset_id == asset_id:
                    return adj.adjudicated_priority

        labels = self.get_labels_for_asset(asset_id, provenance=provenance)
        if not labels:
            return None

        if method == AggregationMethod.MAJORITY_VOTE:
            from collections import Counter
            valid_votes = [l.label for l in labels if l.label != ExpertLabelClass.UNKNOWN]
            if not valid_votes:
                return None
            c = Counter(valid_votes)
            most_common, count = c.most_common(1)[0]
            # Handle ties by abstaining or returning None for tie
            if sum(1 for val in c.values() if val == count) > 1:
                return None
            return most_common

        if method == AggregationMethod.EXPERT_CONSENSUS:
            valid_votes = {l.label for l in labels if l.label != ExpertLabelClass.UNKNOWN}
            if len(valid_votes) == 1:
                return valid_votes.pop()
            return None

        return None
