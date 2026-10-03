from src.risk.factors import FactorValue

CRITICALITY_MAP = {
    "LOW": 0.25,
    "MEDIUM": 0.5,
    "HIGH": 0.75,
    "CRITICAL": 1.0,
    "UNKNOWN": None
}

def extract_asset_criticality(metadata: dict) -> FactorValue:
    # Check explicitly provided business/service/system criticality
    crit = metadata.get("business_criticality") or metadata.get("service_criticality") or metadata.get("system_criticality")
    
    if crit:
        crit = crit.upper()
        if crit in CRITICALITY_MAP and crit != "UNKNOWN":
            return FactorValue(value=CRITICALITY_MAP[crit], source="explicit metadata", confidence=1.0)
            
    # Default policy: Explicitly unknown
    return FactorValue(value=None, source="not provided", confidence=0.0)
