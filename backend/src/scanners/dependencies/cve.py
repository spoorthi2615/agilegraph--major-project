import os
import re
import json
import tempfile
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

OSV_API_URL = os.environ.get("OSV_API_URL", "https://api.osv.dev/v1/query")

DEFAULT_CACHE_DIR = os.path.realpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "dataset", "cache")
)
DEFAULT_CACHE_FILE = os.path.join(DEFAULT_CACHE_DIR, "osv_cache.json")

ECOSYSTEM_MAP = {
    "python": "PyPI",
    "pypi": "PyPI",
    "pip": "PyPI",
    "java": "Maven",
    "maven": "Maven",
    "go": "Go",
    "golang": "Go",
}

def clean_version_string(version: Optional[str]) -> Optional[str]:
    """Cleans version string to pure semver (e.g., '==3.4.7' -> '3.4.7', '\"^1.2\"' -> '1.2')."""
    if not version:
        return None
    cleaned = version.strip().strip('"').strip("'")
    if any(cleaned.startswith(op) for op in [">=", "<=", ">", "<", "~", "*"]):
        match = re.search(r'[\d]+(?:\.[\d]+)*(?:[a-zA-Z0-9.-]*)', cleaned)
        return match.group(0) if match else None
    cleaned = re.sub(r'^[=^~v]+', '', cleaned)
    return cleaned.strip() or None


class CVEProvider:
    def get_vulnerabilities(self, package_name: str, ecosystem: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Interface for CVE enrichment.
        Returns:
            {"status": "unavailable", ...} if no provider configured or service down.
            {"status": "success", "cves": [...]} if found.
        """
        return {
            "status": "unavailable",
            "reason": "Base provider has no enrichment source",
            "enrichment_date": datetime.now(timezone.utc).isoformat()
        }


class OSVCVEProvider(CVEProvider):
    def __init__(
        self,
        timeout: float = 5.0,
        client: Optional[httpx.Client] = None,
        cache_file: Optional[str] = None
    ):
        self.timeout = float(os.environ.get("OSV_TIMEOUT_SECONDS", timeout))
        self.client = client
        self.cache_file = os.path.realpath(cache_file or DEFAULT_CACHE_FILE)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._cache = data
            except Exception:
                self._cache = {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            dir_name = os.path.dirname(self.cache_file)
            temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="tmp_osv_cache_", suffix=".json")
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
            os.replace(temp_path, self.cache_file)
        except Exception:
            pass

    def get_vulnerabilities(self, package_name: str, ecosystem: str, version: Optional[str] = None) -> Dict[str, Any]:
        enrichment_date = datetime.now(timezone.utc).isoformat()
        
        if os.environ.get("AGILEGRAPH_DISABLE_CVE") == "1":
            return {
                "status": "unavailable",
                "reason": "CVE enrichment disabled via environment",
                "enrichment_date": enrichment_date
            }

        if not package_name or not ecosystem:
            return {
                "status": "unavailable",
                "reason": "Missing package name or ecosystem",
                "enrichment_date": enrichment_date
            }

        mapped_ecosystem = ECOSYSTEM_MAP.get(ecosystem.lower(), ecosystem)
        cleaned_version = clean_version_string(version)

        cache_key = f"{mapped_ecosystem}:{package_name}:{cleaned_version or 'any'}"
        if cache_key in self._cache:
            res = dict(self._cache[cache_key])
            if "enrichment_date" not in res:
                res["enrichment_date"] = enrichment_date
            return res

        payload: Dict[str, Any] = {
            "package": {
                "name": package_name,
                "ecosystem": mapped_ecosystem
            }
        }
        if cleaned_version:
            payload["version"] = cleaned_version

        try:
            if self.client:
                response = self.client.post(OSV_API_URL, json=payload, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(OSV_API_URL, json=payload)

            if response.status_code != 200:
                result = {
                    "status": "unavailable",
                    "error": f"OSV service returned status {response.status_code}",
                    "package": package_name,
                    "version": cleaned_version,
                    "enrichment_date": enrichment_date
                }
                self._cache[cache_key] = result
                self._save_cache()
                return result

            data = response.json()
            vulns = data.get("vulns", [])

            cve_ids = []
            for v in vulns:
                vid = v.get("id", "")
                aliases = v.get("aliases", [])
                cve_candidates = [a for a in aliases if a.startswith("CVE-")]
                if vid.startswith("CVE-"):
                    cve_candidates.append(vid)
                if cve_candidates:
                    cve_ids.extend(cve_candidates)
                elif vid:
                    cve_ids.append(vid)

            seen = set()
            unique_cves = [c for c in cve_ids if not (c in seen or seen.add(c))]

            result = {
                "status": "success",
                "cves": unique_cves,
                "count": len(unique_cves),
                "package": package_name,
                "version": cleaned_version,
                "enrichment_date": enrichment_date
            }
            self._cache[cache_key] = result
            self._save_cache()
            return result

        except (httpx.TimeoutException, httpx.ConnectTimeout) as e:
            result = {
                "status": "unavailable",
                "error": f"OSV service timeout: {e}",
                "package": package_name,
                "version": cleaned_version,
                "enrichment_date": enrichment_date
            }
            self._cache[cache_key] = result
            self._save_cache()
            return result
        except httpx.RequestError as e:
            result = {
                "status": "unavailable",
                "error": f"OSV service request failed: {e}",
                "package": package_name,
                "version": cleaned_version,
                "enrichment_date": enrichment_date
            }
            self._cache[cache_key] = result
            self._save_cache()
            return result
        except Exception as e:
            result = {
                "status": "unavailable",
                "error": f"Unexpected error during CVE enrichment: {e}",
                "package": package_name,
                "version": cleaned_version,
                "enrichment_date": enrichment_date
            }
            self._cache[cache_key] = result
            self._save_cache()
            return result


# Global default provider
_default_provider = OSVCVEProvider()

def get_default_cve_provider() -> CVEProvider:
    return _default_provider

def set_default_cve_provider(provider: CVEProvider):
    global _default_provider
    _default_provider = provider

def enrich_cves(package_name: str, ecosystem: str, version: Optional[str] = None) -> Dict[str, Any]:
    return get_default_cve_provider().get_vulnerabilities(package_name, ecosystem, version)
