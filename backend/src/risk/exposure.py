from src.risk.factors import FactorValue

EXPOSURE_MAP = {
    "INTERNAL": 0.25,
    "RESTRICTED": 0.5,
    "INTERNET_FACING": 1.0,
    "UNKNOWN": None
}

def extract_internet_exposure(metadata: dict, endpoints: list = None) -> FactorValue:
    # Look for explicit metadata
    exposure = metadata.get("network_exposure", "UNKNOWN").upper()
    
    if exposure in EXPOSURE_MAP and exposure != "UNKNOWN":
        return FactorValue(value=EXPOSURE_MAP[exposure], source="explicit metadata", confidence=1.0)

    # Check graph-derived endpoints
    if endpoints:
        best_val = None
        best_source = None
        for ep in endpoints:
            ep_props = ep.get("properties", ep) if isinstance(ep, dict) else getattr(ep, "properties", {})
            ep_exp = ep_props.get("network_exposure", "UNKNOWN").upper()
            if ep_exp == "INTERNET_FACING":
                path_desc = ep_props.get("path") or ep_props.get("url") or "unknown"
                return FactorValue(value=1.0, source=f"detected internet-facing endpoint: {path_desc}", confidence=0.9)
            elif ep_exp == "RESTRICTED":
                if best_val is None or best_val < 0.5:
                    best_val = 0.5
                    best_source = f"detected restricted endpoint: {ep_props.get('path') or 'unknown'}"
            elif ep_exp == "INTERNAL":
                if best_val is None:
                    best_val = 0.25
                    best_source = f"detected internal endpoint: {ep_props.get('path') or 'unknown'}"
        if best_val is not None:
            return FactorValue(value=best_val, source=best_source, confidence=0.8)
        
    # Remote TLS host proves it is remotely reachable, but NOT automatically Internet-facing.
    tls_scanned_host = metadata.get("tls_host")
    if tls_scanned_host and tls_scanned_host not in ("127.0.0.1", "localhost"):
        return FactorValue(value=None, source="insufficient evidence (remote reachable only)", confidence=0.0)
        
    return FactorValue(value=None, source="not provided", confidence=0.0)
