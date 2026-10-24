from src.risk.factors import FactorValue

# LOW, MEDIUM, HIGH, CRITICAL
SENSITIVITY_MAP = {
    "LOW": 0.25,
    "MEDIUM": 0.5,
    "HIGH": 0.75,
    "CRITICAL": 1.0,
    "UNKNOWN": None
}

def extract_data_sensitivity(metadata: dict, sensitive_data_nodes: list = None) -> FactorValue:
    classification = metadata.get("data_classification", "UNKNOWN").upper()
    
    if classification in SENSITIVITY_MAP and classification != "UNKNOWN":
        return FactorValue(
            value=SENSITIVITY_MAP[classification],
            source="explicit metadata",
            confidence=1.0
        )

    # Check graph-derived sensitive data nodes
    if sensitive_data_nodes:
        best_val = None
        best_source = None
        for sd in sensitive_data_nodes:
            sd_props = sd.get("properties", sd) if isinstance(sd, dict) else getattr(sd, "properties", {})
            sd_class = sd_props.get("classification", "UNKNOWN").upper()
            sd_name = sd_props.get("name", "sensitive_data")
            if sd_class in SENSITIVITY_MAP and SENSITIVITY_MAP[sd_class] is not None:
                val = SENSITIVITY_MAP[sd_class]
                if best_val is None or val > best_val:
                    best_val = val
                    best_source = f"detected sensitive data: {sd_name} ({sd_class.lower()})"
        if best_val is not None:
            return FactorValue(value=best_val, source=best_source, confidence=0.85)

    return FactorValue(value=None, source="not provided", confidence=0.0)
