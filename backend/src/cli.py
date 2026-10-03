import argparse
import sys
import json
import networkx as nx
from src.pipeline.runner import run_pipeline
from src.pipeline.reporter import generate_markdown_report

def main():
    parser = argparse.ArgumentParser(description="AgileGraph CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    scan_parser = subparsers.add_parser("scan", help="Run heuristic scan on a repository")
    scan_parser.add_argument("repository", help="Path to the repository to scan")
    scan_parser.add_argument("--output", help="Path to output JSON file", required=True)
    scan_parser.add_argument("--project-id", help="Project ID for the scan", default="local-scan")
    scan_parser.add_argument("--missing-data-policy", help="Missing data policy (STRICT or RENORMALIZE)", choices=["STRICT", "RENORMALIZE"], default="RENORMALIZE")
    
    report_parser = subparsers.add_parser("report", help="Generate a human-readable Markdown report from a JSON scan")
    report_parser.add_argument("input", help="Path to input JSON scan file")
    report_parser.add_argument("--format", help="Format of the output report", choices=["markdown"], default="markdown")
    report_parser.add_argument("--output", help="Path to output Markdown file (defaults to stdout if not provided)")
    
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
        
    elif args.command == "report":
        try:
            out_path = args.output if args.output else args.input.replace(".json", ".md")
            generate_markdown_report(args.input, out_path)
            print(f"Report successfully generated at {out_path}")
        except Exception as e:
            print(f"Error generating report: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
