from typing import List, Dict, Any

class CVEProvider:
    def get_vulnerabilities(self, package_name: str, ecosystem: str, version: str) -> Dict[str, Any]:
        """
        Interface for CVE enrichment.
        Returns:
            {"status": "unavailable"} if no provider configured.
            {"status": "success", "cves": [...]} if found.
        """
        # Initially unimplemented as per research constraints
        return {"status": "unavailable"}

def enrich_cves(package_name: str, ecosystem: str, version: str) -> Dict[str, Any]:
    provider = CVEProvider()
    return provider.get_vulnerabilities(package_name, ecosystem, version)
