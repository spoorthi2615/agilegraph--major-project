import re
from typing import List, Optional, Dict, Any
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

# Python route decorators
PY_ROUTE_PATTERN = re.compile(
    r'@(?:app|router|bp|api)\.(get|post|put|delete|patch|options|head|route)\s*\(\s*["\']([^"\']+)["\']'
)

# Python server listeners
PY_SERVER_RUN_PATTERN = re.compile(
    r'\b(?:uvicorn\.run|app\.run|HTTPServer)\s*\((?:[^)]*host\s*=\s*["\']([^"\']+)["\'])?(?:[^)]*port\s*=\s*(\d+))?'
)

# Python outgoing HTTP requests
PY_HTTP_CLIENT_PATTERN = re.compile(
    r'\b(?:requests|httpx|urllib\.request)\.(get|post|put|delete|patch|head|urlopen)\s*\(\s*["\'](https?://[^"\']+)["\']'
)

# Java Spring & JAX-RS mappings
JAVA_ROUTE_PATTERN = re.compile(
    r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping|Path)\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?'
)

# Java outgoing HTTP requests
JAVA_HTTP_CLIENT_PATTERN = re.compile(
    r'(?:new\s+URL|URI\.create)\s*\(\s*["\'](https?://[^"\']+)["\']'
)

# Go HTTP routes
GO_ROUTE_PATTERN = re.compile(
    r'\b(?:http\.HandleFunc|http\.Handle|[a-zA-Z0-9_]+\.(?:GET|POST|PUT|DELETE|PATCH|Handle|HandleFunc))\s*\(\s*["\']([^"\']+)["\']'
)

# Go server listeners
GO_SERVER_RUN_PATTERN = re.compile(
    r'\bhttp\.(ListenAndServe(?:TLS)?)\s*\(\s*["\']([^"\']*)["\']'
)

# Go outgoing HTTP requests
GO_HTTP_CLIENT_PATTERN = re.compile(
    r'\bhttp\.(Get|Post|Head)\s*\(\s*["\'](https?://[^"\']+)["\']'
)

# General URL pattern in strings
GENERIC_URL_PATTERN = re.compile(r'["\'](https?://[a-zA-Z0-9_.:-]+(?:/[^"\'\s]*)?)["\']')


def classify_exposure(host: Optional[str], url: Optional[str]) -> str:
    if host in ("0.0.0.0", "::"):
        return "INTERNET_FACING"
    if host in ("127.0.0.1", "localhost", "::1"):
        return "INTERNAL"
    if url:
        if "127.0.0.1" in url or "localhost" in url or ".internal" in url:
            return "INTERNAL"
        if url.startswith("https://") or url.startswith("http://"):
            return "INTERNET_FACING"
    return "UNKNOWN"


def scan_endpoints(repository: str, filepath: str, code: str, language: Language) -> List[FindingRecord]:
    findings = []
    lines = code.split('\n')

    for i, line in enumerate(lines, start=1):
        # 1. Python Route Detection
        if language == Language.PYTHON:
            for match in PY_ROUTE_PATTERN.finditer(line):
                method_raw = match.group(1).upper()
                method = "ALL" if method_raw == "ROUTE" else method_raw
                path = match.group(2)
                exposure = "UNKNOWN"
                
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.PYTHON,
                    api=f"route:{method}:{path}",
                    operation="endpoint_declaration",
                    evidence=line.strip(),
                    confidence=0.95,
                    extra={
                        "path": path,
                        "method": method,
                        "protocol": "HTTP",
                        "network_exposure": exposure
                    }
                ))

            for match in PY_SERVER_RUN_PATTERN.finditer(line):
                host = match.group(1) or "127.0.0.1"
                port = int(match.group(2)) if match.group(2) else 8000
                exposure = classify_exposure(host, None)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.PYTHON,
                    api=f"server_bind:{host}:{port}",
                    operation="server_listener",
                    evidence=line.strip(),
                    confidence=0.95,
                    extra={
                        "host": host,
                        "port": port,
                        "network_exposure": exposure
                    }
                ))

            for match in PY_HTTP_CLIENT_PATTERN.finditer(line):
                method = match.group(1).upper()
                url = match.group(2)
                protocol = "HTTPS" if url.startswith("https://") else "HTTP"
                exposure = classify_exposure(None, url)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.PYTHON,
                    api=f"client_call:{url}",
                    operation="endpoint_client",
                    evidence=line.strip(),
                    confidence=0.9,
                    extra={
                        "url": url,
                        "method": method,
                        "protocol": protocol,
                        "network_exposure": exposure
                    }
                ))

        # 2. Java Route Detection
        elif language == Language.JAVA:
            for match in JAVA_ROUTE_PATTERN.finditer(line):
                ann = match.group(1)
                method_map = {
                    "GetMapping": "GET",
                    "PostMapping": "POST",
                    "PutMapping": "PUT",
                    "DeleteMapping": "DELETE",
                    "PatchMapping": "PATCH",
                    "RequestMapping": "ALL",
                    "Path": "ALL"
                }
                method = method_map.get(ann, "ALL")
                path = match.group(2) or "/"
                
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.JAVA,
                    api=f"route:{method}:{path}",
                    operation="endpoint_declaration",
                    evidence=line.strip(),
                    confidence=0.95,
                    extra={
                        "path": path,
                        "method": method,
                        "protocol": "HTTP",
                        "network_exposure": "UNKNOWN"
                    }
                ))

            for match in JAVA_HTTP_CLIENT_PATTERN.finditer(line):
                url = match.group(1)
                protocol = "HTTPS" if url.startswith("https://") else "HTTP"
                exposure = classify_exposure(None, url)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.JAVA,
                    api=f"client_call:{url}",
                    operation="endpoint_client",
                    evidence=line.strip(),
                    confidence=0.9,
                    extra={
                        "url": url,
                        "method": "ALL",
                        "protocol": protocol,
                        "network_exposure": exposure
                    }
                ))

        # 3. Go Route Detection
        elif language == Language.GO:
            for match in GO_ROUTE_PATTERN.finditer(line):
                path = match.group(1)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.GO,
                    api=f"route:{path}",
                    operation="endpoint_declaration",
                    evidence=line.strip(),
                    confidence=0.95,
                    extra={
                        "path": path,
                        "method": "ALL",
                        "protocol": "HTTP",
                        "network_exposure": "UNKNOWN"
                    }
                ))

            for match in GO_SERVER_RUN_PATTERN.finditer(line):
                api_func = match.group(1)
                addr = match.group(2)
                protocol = "HTTPS" if "TLS" in api_func else "HTTP"
                host = addr.split(':')[0] if ':' in addr else addr
                port = int(addr.split(':')[1]) if ':' in addr and addr.split(':')[1].isdigit() else (443 if protocol == "HTTPS" else 80)
                exposure = classify_exposure(host or "0.0.0.0", None)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.GO,
                    api=f"server_bind:{addr or ':80'}",
                    operation="server_listener",
                    evidence=line.strip(),
                    confidence=0.95,
                    extra={
                        "host": host or "0.0.0.0",
                        "port": port,
                        "protocol": protocol,
                        "network_exposure": exposure
                    }
                ))

            for match in GO_HTTP_CLIENT_PATTERN.finditer(line):
                method = match.group(1).upper()
                url = match.group(2)
                protocol = "HTTPS" if url.startswith("https://") else "HTTP"
                exposure = classify_exposure(None, url)
                findings.append(FindingRecord(
                    asset_type=AssetType.ENDPOINT,
                    repository=repository,
                    file=filepath,
                    line=i,
                    language=Language.GO,
                    api=f"client_call:{url}",
                    operation="endpoint_client",
                    evidence=line.strip(),
                    confidence=0.9,
                    extra={
                        "url": url,
                        "method": method,
                        "protocol": protocol,
                        "network_exposure": exposure
                    }
                ))

    return findings
