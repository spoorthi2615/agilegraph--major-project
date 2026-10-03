from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import datetime

class ExpertLabelClass(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN" # Represents abstention/cannot assess

class Expert(BaseModel):
    expert_id: str # Pseudonymous identifier (e.g. expert_01)
    # No PII stored here to respect privacy model

class AssetForReview(BaseModel):
    asset_id: str
    project_id: str
    heuristic_score: Optional[float] = None # Used ONLY as a comparator, NEVER as label

class ExpertLabel(BaseModel):
    asset_id: str
    project_id: str
    expert_id: str
    label: ExpertLabelClass
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    dataset_version: str
    annotation_protocol_version: str

class ValidationSession(BaseModel):
    session_id: str
    expert_id: str
    labels: List[ExpertLabel]

class AggregationMethod(str, Enum):
    MAJORITY_VOTE = "MAJORITY_VOTE"
    ADJUDICATION = "ADJUDICATION"
    EXPERT_CONSENSUS = "EXPERT_CONSENSUS"

class ValidationDataset(BaseModel):
    dataset_version: str
    annotation_protocol_version: str
    assets: List[AssetForReview]
    sessions: List[ValidationSession]
    
    def get_labels_for_asset(self, asset_id: str) -> List[ExpertLabel]:
        labels = []
        for s in self.sessions:
            for l in s.labels:
                if l.asset_id == asset_id:
                    labels.append(l)
        return labels

    def get_consensus(self, asset_id: str, method: AggregationMethod) -> Optional[ExpertLabelClass]:
        labels = self.get_labels_for_asset(asset_id)
        if not labels:
            return None
            
        if method == AggregationMethod.MAJORITY_VOTE:
            from collections import Counter
            valid_votes = [l.label for l in labels if l.label != ExpertLabelClass.UNKNOWN]
            if not valid_votes:
                return None
            c = Counter(valid_votes)
            most_common, count = c.most_common(1)[0]
            # Handle ties by abstaining or relying on adjudication - returning None for simple tie
            if sum(1 for val in c.values() if val == count) > 1:
                return None 
            return most_common
        
        # Other methods would require manual input or distinct data structures
        return None
