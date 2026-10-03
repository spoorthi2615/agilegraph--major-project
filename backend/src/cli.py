import argparse
import sys
import json
import networkx as nx
from src.pipeline.runner import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="AgileGraph CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    scan_parser = subparsers.add_parser("scan", help="Run heuristic scan on a repository")
    scan_parser.add_argument("repository", help="Path to the repository to scan")
    scan_parser.add_argument("--output", help="Path to output JSON file", required=True)
    scan_parser.add_argument("--project-id", help="Project ID for the scan", default="local-scan")
    scan_parser.add_argument("--missing-data-policy", help="Missing data policy (STRICT or RENORMALIZE)", choices=["STRICT", "RENORMALIZE"], default="RENORMALIZE")
    
    args = parser.parse_args()
    
    if args.command == "scan":
        try:
            result = run_pipeline(args.repository, args.project_id, args.missing_data_policy)
        except Exception as e:
            print(f"Error during scan: {e}", file=sys.stderr)
            sys.exit(1)
            
        g = result["graph"]
        graph_data = nx.node_link_data(g)
        
        output_payload = {
            "project_id": args.project_id,
            "analysis_type": "HEURISTIC",
            "ml_status": "BLOCKED",
            "expert_validation_status": "BLOCKED",
            "missing_data_policy": args.missing_data_policy,
            "provenance": result["provenance"],
            "assets": result["scores"],
            "graph": {
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", [])
            }
        }
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
            
        print(f"Scan complete. Found {len(g.nodes)} nodes and {len(result['scores'])} vulnerable assets.")
        print(f"Report written to {args.output}")

if __name__ == "__main__":
    main()
