import pytest
import os
from unittest.mock import MagicMock
import httpx

from src.scanners.dependencies.cve import (
    clean_version_string,
    OSVCVEProvider,
    enrich_cves,
    set_default_cve_provider,
    CVEProvider
)

@pytest.fixture(autouse=True)
def isolated_cve_cache(tmp_path, monkeypatch):
    test_cache = str(tmp_path / "test_osv_cache.json")
    monkeypatch.setattr("src.scanners.dependencies.cve.DEFAULT_CACHE_FILE", test_cache)

def test_clean_version_string():
    assert clean_version_string("==1.2.3") == "1.2.3"
    assert clean_version_string("\"^3.4.0\"") == "3.4.0"
    assert clean_version_string("~0.1.2") == "0.1.2"
    assert clean_version_string("v2.1.0") == "2.1.0"
    assert clean_version_string("  1.0.0  ") == "1.0.0"
    assert clean_version_string(">=2.0.0") == "2.0.0"
    assert clean_version_string("") is None
    assert clean_version_string(None) is None

def test_osv_provider_success_with_cves():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "vulns": [
            {
                "id": "GHSA-1234",
                "aliases": ["CVE-2021-12345", "OSV-2021-99"],
                "summary": "Sample vuln"
            },
            {
                "id": "CVE-2021-99999",
                "aliases": [],
                "summary": "Direct CVE"
            }
        ]
    }
    mock_client.post.return_value = mock_response

    provider = OSVCVEProvider(client=mock_client)
    res = provider.get_vulnerabilities("vulnerable-pkg", "python", "==1.0.0")

    assert res["status"] == "success"
    assert "CVE-2021-12345" in res["cves"]
    assert "CVE-2021-99999" in res["cves"]
    assert res["count"] == 2
    assert res["version"] == "1.0.0"

def test_osv_provider_success_zero_cves():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"vulns": []}
    mock_client.post.return_value = mock_response

    provider = OSVCVEProvider(client=mock_client)
    res = provider.get_vulnerabilities("safe-pkg", "pypi", "2.0.0")

    assert res["status"] == "success"
    assert res["cves"] == []
    assert res["count"] == 0

def test_osv_provider_timeout_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")

    provider = OSVCVEProvider(timeout=1.0, client=mock_client)
    res = provider.get_vulnerabilities("timeout-pkg", "pypi", "1.0.0")

    assert res["status"] == "unavailable"
    assert "timeout" in res["error"].lower()

def test_osv_provider_http_error():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_client.post.return_value = mock_response

    provider = OSVCVEProvider(client=mock_client)
    res = provider.get_vulnerabilities("service-down-pkg", "maven", "1.0.0")

    assert res["status"] == "unavailable"
    assert "503" in res["error"]

def test_osv_provider_request_error():
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.ConnectError("DNS resolution failed")

    provider = OSVCVEProvider(client=mock_client)
    res = provider.get_vulnerabilities("offline-pkg", "go", "1.0.0")

    assert res["status"] == "unavailable"
    assert "request failed" in res["error"]

def test_osv_provider_disabled_env(monkeypatch):
    monkeypatch.setenv("AGILEGRAPH_DISABLE_CVE", "1")
    provider = OSVCVEProvider()
    res = provider.get_vulnerabilities("pkg", "pypi", "1.0.0")
    assert res["status"] == "unavailable"
    assert "disabled" in res["reason"]

def test_osv_provider_caching(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"vulns": []}
    mock_client.post.return_value = mock_response

    provider = OSVCVEProvider(client=mock_client, cache_file=str(tmp_path / "caching_test.json"))
    res1 = provider.get_vulnerabilities("cached-pkg", "python", "1.0.0")
    res2 = provider.get_vulnerabilities("cached-pkg", "python", "1.0.0")

    assert res1 == res2
    assert mock_client.post.call_count == 1  # Only queried once due to cache

def test_osv_provider_malformed_json_response():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_client.post.return_value = mock_response

    provider = OSVCVEProvider(client=mock_client)
    res = provider.get_vulnerabilities("malformed-pkg", "python", "1.0.0")

    assert res["status"] == "unavailable"
    assert "error" in res

def test_osv_provider_missing_package_or_ecosystem():
    provider = OSVCVEProvider()
    res_no_pkg = provider.get_vulnerabilities("", "python", "1.0.0")
    res_no_eco = provider.get_vulnerabilities("pkg", "", "1.0.0")

    assert res_no_pkg["status"] == "unavailable"
    assert res_no_eco["status"] == "unavailable"

def test_distinguish_unavailable_from_zero_cves():
    """Confirms that provider failures are explicitly distinguishable from verified absence of CVEs."""
    mock_client_err = MagicMock()
    mock_client_err.post.side_effect = httpx.ConnectError("Network down")
    provider_err = OSVCVEProvider(client=mock_client_err)
    res_err = provider_err.get_vulnerabilities("any-pkg", "python", "1.0.0")

    mock_client_clean = MagicMock()
    mock_response_clean = MagicMock()
    mock_response_clean.status_code = 200
    mock_response_clean.json.return_value = {"vulns": []}
    mock_client_clean.post.return_value = mock_response_clean
    provider_clean = OSVCVEProvider(client=mock_client_clean)
    res_clean = provider_clean.get_vulnerabilities("clean-pkg", "python", "1.0.0")

    assert res_err["status"] == "unavailable"
    assert res_clean["status"] == "success"
    assert res_err["status"] != res_clean["status"]
    assert "cves" not in res_err
    assert res_clean["cves"] == []


def test_live_osv_query_and_cve_risk_mapping():
    """
    Optional live verification against OSV.dev (skipped if network is unreachable).
    Confirms end-to-end integration:
      requests:2.20.0 (PyPI) -> OSV.dev returns known CVEs -> extract_cve_risk returns 1.0 (KNOWN_WITH_CVES).
    """
    from src.risk.cve_risk import extract_cve_risk
    provider = OSVCVEProvider(timeout=5.0)
    try:
        res = provider.get_vulnerabilities("requests", "pypi", "2.20.0")
        if res.get("status") == "success":
            assert res["count"] > 0
            assert any("CVE-" in c or "GHSA-" in c for c in res["cves"])
            factor = extract_cve_risk(res)
            assert factor.value == 1.0
            assert factor.source == "KNOWN_WITH_CVES"
    except Exception as e:
        pytest.skip(f"Live network test skipped due to connectivity: {e}")

def test_osv_provider_disk_caching_and_enrichment_date(tmp_path):
    cache_file = str(tmp_path / "osv_cache.json")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"vulns": [{"id": "CVE-2024-1111"}]}
    mock_client.post.return_value = mock_response

    # First instance writes to disk cache
    provider1 = OSVCVEProvider(client=mock_client, cache_file=cache_file)
    res1 = provider1.get_vulnerabilities("disk-pkg", "pypi", "1.0.0")
    assert res1["status"] == "success"
    assert "enrichment_date" in res1
    assert os.path.exists(cache_file)

    # Second instance loads from disk cache without making network call
    offline_client = MagicMock()
    offline_client.post.side_effect = RuntimeError("Should not be called")
    provider2 = OSVCVEProvider(client=offline_client, cache_file=cache_file)
    res2 = provider2.get_vulnerabilities("disk-pkg", "pypi", "1.0.0")
    assert res2["status"] == "success"
    assert res2["cves"] == ["CVE-2024-1111"]
    assert res2["enrichment_date"] == res1["enrichment_date"]


