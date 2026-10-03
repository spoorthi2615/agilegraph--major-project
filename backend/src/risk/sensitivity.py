from src.risk.factors import FactorValue

# LOW, MEDIUM, HIGH, CRITICAL
SENSITIVITY_MAP = {
    "LOW": 0.25,
    "MEDIUM": 0.5,
    "HIGH": 0.75,
    "CRITICAL": 1.0,
    "UNKNOWN": None
}

def extract_data_sensitivity(metadata: dict) -> FactorValue:
    classification = metadata.get("data_classification", "UNKNOWN").upper()
    
    if classification in SENSITIVITY_MAP and classification != "UNKNOWN":
        return FactorValue(
            value=SENSITIVITY_MAP[classification],
            source="explicit metadata",
            confidence=1.0
        )
    return FactorValue(value=None, source="not provided", confidence=0.0)
