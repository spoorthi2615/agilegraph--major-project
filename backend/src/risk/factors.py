from pydantic import BaseModel
from typing import Optional, Any

class FactorValue(BaseModel):
    value: Optional[float] = None
    source: str
    confidence: float

class RiskFactors(BaseModel):
    data_sensitivity: FactorValue
    asset_criticality: FactorValue
    internet_exposure: FactorValue
    crypto_weakness: FactorValue
    cve_risk: FactorValue
    library_centrality: FactorValue
    migration_difficulty: FactorValue
