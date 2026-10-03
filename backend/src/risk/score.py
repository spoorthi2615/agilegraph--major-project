from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum
from src.risk.weights import HeuristicWeights
from src.risk.factors import RiskFactors

class MissingDataPolicy(str, Enum):
    STRICT = "STRICT"
    RENORMALIZE = "RENORMALIZE"

class FactorContribution(BaseModel):
    value: float
    weight: float
    contribution: float

class RiskScoreResult(BaseModel):
    score: float
    scale: str = "0.0-1.0"
    formula_version: str
    weights: dict
    factors: dict
    weighted_contributions: Dict[str, FactorContribution]
    missing_factors: List[str]
    missing_data_policy: MissingDataPolicy
    assumptions: List[str]
