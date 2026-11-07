"""
Expert Validation Schema and Data Management Module for AgileGraph.

This module provides data structures and adjudication pipelines for independent
human expert evaluation of post-quantum cryptographic risk rankings.

Methodological Constraints:
1. Expert labels MUST remain strictly segregated from GATv2 training/validation splits.
2. Under NO circumstances should expert annotations be used to fit or fine-tune the GNN.
3. In accordance with scientific integrity guidelines, annotations are collected externally;
   synthetic or fabricated expert labels are strictly prohibited in official evaluations.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ExpertLabelClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


LABEL_TO_INT: Dict[ExpertLabelClass, int] = {
    ExpertLabelClass.LOW: 0,
    ExpertLabelClass.MEDIUM: 1,
    ExpertLabelClass.HIGH: 2
}

INT_TO_LABEL: Dict[int, ExpertLabelClass] = {v: k for k, v in LABEL_TO_INT.items()}


class Expert(BaseModel):
    expert_id: str
    name: Optional[str] = "Anonymous Reviewer"
    years_experience: Optional[float] = None
    role: Optional[str] = "Security Reviewer"
    affiliation: Optional[str] = None


class AssetForReview(BaseModel):
    asset_id: str
    repository: str
    file_path: str
    snippet: Optional[str] = None
    detected_algorithms: List[str] = Field(default_factory=list)
    heuristic_factors: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @classmethod
    def canonical_id(cls, repository: str, file_path: str) -> str:
        """Constructs repository-scoped canonical asset key matching graph node_ids."""
        clean_repo = str(repository).strip()
        clean_path = str(file_path).strip()
        if clean_path.startswith(f"{clean_repo}:"):
            return clean_path
        return f"{clean_repo}:{clean_path}"


class ExpertLabel(BaseModel):
    asset_id: str
    expert_id: str
    label: ExpertLabelClass
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Reviewer confidence score (0.0 to 1.0)")
    rationale: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    repository: Optional[str] = None

    def canonical_asset_id(self) -> str:
        """Returns the canonical repository-scoped asset key."""
        if self.repository and not self.asset_id.startswith(f"{self.repository}:"):
            return f"{self.repository}:{self.asset_id}"
        return self.asset_id

    def sync_aliases(self) -> None:
        """Normalizes label formatting if needed."""
        if isinstance(self.label, str):
            clean_str = self.label.strip().upper()
            if clean_str in ExpertLabelClass.__members__:
                self.label = ExpertLabelClass[clean_str]


class AdjudicatedLabel(BaseModel):
    asset_id: str
    consensus_label: ExpertLabelClass
    agreement_score: float = Field(description="Proportion of reviewers agreeing on the consensus label")
    label_distribution: Dict[str, int]
    adjudication_method: str = "MAJORITY"  # "MAJORITY", "UNANIMOUS", "RESOLVED_TIE"


class ValidationSession(BaseModel):
    session_id: str
    date: datetime = Field(default_factory=datetime.utcnow)
    experts: List[Expert] = Field(default_factory=list)
    assets_reviewed: List[str] = Field(default_factory=list)


class ValidationDataset(BaseModel):
    dataset_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = "Independent Expert Validation Reference Corpus"
    experts: List[Expert] = Field(default_factory=list)
    assets: List[AssetForReview] = Field(default_factory=list)
    labels: List[ExpertLabel] = Field(default_factory=list)
    adjudicated_labels: List[AdjudicatedLabel] = Field(default_factory=list)

    def get_labels_for_asset(self, asset_id: str) -> List[ExpertLabel]:
        return [
            lbl for lbl in self.labels
            if lbl.asset_id == asset_id or lbl.canonical_asset_id() == asset_id
        ]

    def get_expert_labels(self, expert_id: str) -> List[ExpertLabel]:
        return [lbl for lbl in self.labels if lbl.expert_id == expert_id]

    def deduplicate_labels(self) -> int:
        """
        Deduplicates multiple annotations from the same expert on the same canonical asset.
        If consistent, retains highest confidence. If contradictory, conservative
        precedence is applied (HIGH > MEDIUM > LOW).
        Returns the number of duplicate labels removed.
        """
        initial_count = len(self.labels)
        deduped: Dict[tuple, ExpertLabel] = {}
        order = ["HIGH", "MEDIUM", "LOW"]

        for lbl in self.labels:
            key = (lbl.expert_id, lbl.canonical_asset_id())
            if key not in deduped:
                deduped[key] = lbl
            else:
                existing = deduped[key]
                chosen_label = existing.label if order.index(existing.label.value) <= order.index(lbl.label.value) else lbl.label
                max_conf = max(existing.confidence, lbl.confidence)
                notes = existing.rationale if existing.rationale == lbl.rationale else f"{existing.rationale}; {lbl.rationale}".strip("; ")
                deduped[key] = ExpertLabel(
                    asset_id=existing.asset_id,
                    expert_id=lbl.expert_id,
                    label=chosen_label,
                    confidence=max_conf,
                    rationale=notes,
                    repository=existing.repository or lbl.repository
                )

        self.labels = list(deduped.values())
        return initial_count - len(self.labels)

    def adjudicate(self, strategy: str = "MAJORITY") -> List[AdjudicatedLabel]:
        """
        Adjudicates multi-expert consensus per asset without consulting heuristic scores.
        Automatically deduplicates multiple labels per (expert, asset) before adjudication.
        """
        self.deduplicate_labels()
        asset_ids = {a.asset_id for a in self.assets}
        adjudicated = []

        for a_id in sorted(list(asset_ids)):
            asset_labels = self.get_labels_for_asset(a_id)
            if not asset_labels:
                continue

            dist: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
            for lbl in asset_labels:
                dist[lbl.label.value] += 1

            total = len(asset_labels)
            max_count = max(dist.values())
            top_classes = [c for c, count in dist.items() if count == max_count]

            if len(top_classes) == 1:
                consensus_val = top_classes[0]
                method = "UNANIMOUS" if max_count == total else "MAJORITY"
            else:
                # Deterministic tie-breaker: highest risk takes conservative precedence
                order = ["HIGH", "MEDIUM", "LOW"]
                consensus_val = next(c for c in order if c in top_classes)
                method = "RESOLVED_TIE"

            adj = AdjudicatedLabel(
                asset_id=a_id,
                consensus_label=ExpertLabelClass(consensus_val),
                agreement_score=round(max_count / total, 4),
                label_distribution=dist,
                adjudication_method=method
            )
            adjudicated.append(adj)

        self.adjudicated_labels = adjudicated
        return adjudicated

