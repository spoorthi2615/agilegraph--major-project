from src.risk.factors import FactorValue

EXPOSURE_MAP = {
    "INTERNAL": 0.25,
    "RESTRICTED": 0.5,
    "INTERNET_FACING": 1.0,
    "UNKNOWN": None
}

def extract_internet_exposure(metadata: dict) -> FactorValue:
    # Look for explicit metadata
    exposure = metadata.get("network_exposure", "UNKNOWN").upper()
    
    if exposure in EXPOSURE_MAP and exposure != "UNKNOWN":
        return FactorValue(value=EXPOSURE_MAP[exposure], source="explicit metadata", confidence=1.0)
        
    # Remote TLS host proves it is remotely reachable, but NOT automatically Internet-facing.
    tls_scanned_host = metadata.get("tls_host")
    if tls_scanned_host and tls_scanned_host not in ("127.0.0.1", "localhost"):
        return FactorValue(value=None, source="insufficient evidence (remote reachable only)", confidence=0.0)
        
    return FactorValue(value=None, source="not provided", confidence=0.0)
