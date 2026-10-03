from src.risk.factors import FactorValue

# These are initial prototype thresholds. 
# They are not empirically validated thresholds.
# They are not final scientific weights.
DEFAULT_MIGRATION_THRESHOLDS = {
    "code_change_max": 10.0,
    "dep_change_max": 5.0,
    "cert_change_max": 2.0,
    "infra_change_max": 2.0
}
DEFAULT_MIGRATION_WEIGHTS = {
    "code_change": 0.4,
    "dep_change": 0.3,
    "cert_change": 0.2,
    "infra_change": 0.1
}

def extract_migration_difficulty(inputs: dict, thresholds: dict = None, weights: dict = None) -> FactorValue:
    """
    Inputs map:
    - code_change (int): Number of affected files
    - dependency_change (int): Number of dependent libraries to swap
    - certificate_change (int): Certificates to replace
    - infrastructure_change (int): Endpoints to reconfigure
    """
    if thresholds is None:
        thresholds = DEFAULT_MIGRATION_THRESHOLDS
    if weights is None:
        weights = DEFAULT_MIGRATION_WEIGHTS
        
    # If no explicit inputs are provided, we don't invent a formula
    if not inputs:
        return FactorValue(value=None, source="no inputs provided", confidence=0.0)
        
    code_change = inputs.get("code_change", 0)
    dep_change = inputs.get("dependency_change", 0)
    cert_change = inputs.get("certificate_change", 0)
    infra_change = inputs.get("infrastructure_change", 0)
    
    score = (
        min(code_change / thresholds["code_change_max"], 1.0) * weights["code_change"] +
        min(dep_change / thresholds["dep_change_max"], 1.0) * weights["dep_change"] +
        min(cert_change / thresholds["cert_change_max"], 1.0) * weights["cert_change"] +
        min(infra_change / thresholds["infra_change_max"], 1.0) * weights["infra_change"]
    )
    
    return FactorValue(
        value=score, 
        source="deterministic component model (initial prototype weights)", 
        confidence=0.8
    )
