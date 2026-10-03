import argparse
from typing import List
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType

def scan_tls_endpoint(host: str, port: int, authorized: bool) -> List[FindingRecord]:
    if not authorized:
        raise PermissionError("Active scanning requires the --authorized flag. Scanning unauthorized third-party infrastructure is strictly prohibited.")
    
    # Mock implementation of TLS scan for localhost tests
    findings = []
    if host in ("127.0.0.1", "localhost"):
        findings.append(FindingRecord(
            asset_type=AssetType.ENDPOINT,
            repository="live_infrastructure",
            evidence=f"Scanned {host}:{port}",
            confidence=1.0,
            extra={"host": host, "port": port, "tls_version": "TLSv1.2"}
        ))
    return findings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TLS Scanner")
    parser.add_argument("--host", required=True, help="Target host")
    parser.add_argument("--port", type=int, default=443, help="Target port")
    parser.add_argument("--authorized", action="store_true", help="Explicitly authorize active scanning")
    args = parser.parse_args()
    
    try:
        results = scan_tls_endpoint(args.host, args.port, args.authorized)
        for r in results:
            print(r.model_dump_json())
    except PermissionError as e:
        print(f"Error: {e}")
