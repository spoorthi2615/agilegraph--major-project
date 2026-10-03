from src.risk.factors import FactorValue

def extract_cve_risk(cve_info: dict) -> FactorValue:
    """
    cve_info should come from CVEProvider interface:
    {"status": "unavailable"} -> UNAVAILABLE
    {"status": "success", "cves": [...]} -> KNOWN_WITH_CVES or KNOWN_WITHOUT_CVES
    """
    status = cve_info.get("status", "unavailable")
    
    if status == "unavailable":
        return FactorValue(value=None, source="CVE provider unavailable", confidence=0.0)
        
    cves = cve_info.get("cves", [])
    if len(cves) > 0:
        # A simple normalization for prototype: any CVE gives high risk
        return FactorValue(value=1.0, source="KNOWN_WITH_CVES", confidence=1.0)
    else:
        return FactorValue(value=0.0, source="KNOWN_WITHOUT_CVES", confidence=1.0)
