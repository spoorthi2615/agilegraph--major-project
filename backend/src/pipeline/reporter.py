import json
import sys
from datetime import datetime

def generate_markdown_report(json_path: str, output_path: str):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to read or parse JSON file: {e}")
        
    required_keys = ["project_id", "analysis_type", "ml_status", "expert_validation_status", "missing_data_policy", "provenance", "assets", "graph"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"Missing required field in JSON payload: {k}")
            
    # Write report
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"# AgileGraph Security Audit Report\n\n")
        out.write(f"**Project ID**: `{data['project_id']}`\n")
        out.write(f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        # RESEARCH STATUS (MANDATORY)
        out.write(f"## ⚠️ RESEARCH STATUS & INTEGRITY GATE\n\n")
        out.write(f"This report presents a **{data['analysis_type']} ANALYSIS** generated through static code scanning and rule-based priors. It is designed for human review and expert annotation.\n\n")
        out.write(f"- **GATv2**: `PENDING_EXPERT_LABELS`\n")
        out.write(f"- **Expert validation**: `{data['expert_validation_status']}`\n")
        out.write(f"- **Empirical evaluation**: `{data['ml_status']}`\n\n")
        out.write(f"> **Important**: No fabricated empirical metrics, kappa scores, F1/accuracy results, or p-values are claimed in this report.\n\n")
        
        # SCAN SUMMARY
        out.write(f"## Scan Summary\n\n")
        out.write(f"- **Scanned Files**: {data['provenance'].get('scanned_files', 0)}\n")
        out.write(f"- **Missing Data Policy**: `{data['missing_data_policy']}`\n")
        out.write(f"- **Total Nodes Found**: {len(data['graph']['nodes'])}\n")
        out.write(f"- **Vulnerable Assets Identified**: {len(data['assets'])}\n\n")
        
        # ASSET DETAILS
        out.write(f"## Heuristic Risk Results\n\n")
        
        if not data['assets']:
            out.write("No vulnerable assets detected.\n")
        
        for idx, asset in enumerate(data['assets']):
            out.write(f"### Asset {idx + 1}: `{asset['asset_id']}`\n\n")
            out.write(f"**Heuristic Score**: {asset['score']} (Scale: {asset.get('scale', '0.0-1.0')})\n\n")
            
            if asset.get('missing_factors'):
                out.write(f"**Missing Contextual Factors**: {', '.join(asset['missing_factors'])}\n\n")
            
            out.write(f"#### Factor Contributions\n\n")
            out.write(f"| Factor | Value | Weight | Contribution | Source |\n")
            out.write(f"|---|---|---|---|---|\n")
            
            factors = asset.get('factors', {})
            weights = asset.get('weights', {})
            weighted = asset.get('weighted_contributions', {})
            
            for f_name, f_data in factors.items():
                val = f_data.get('value', 'null')
                if val is None: val = 'null'
                w = weights.get(f_name, 0.0)
                cont_data = weighted.get(f_name, {})
                cont = cont_data.get('contribution', 0.0)
                source = f_data.get('source', 'unknown')
                
                out.write(f"| {f_name} | {val} | {w:.4f} | {cont:.4f} | {source} |\n")
            
            out.write(f"\n#### Traceability & Scanner Evidence\n\n")
            # Find evidence nodes for this asset in the graph
            evidence_lines = []
            asset_id = asset['asset_id']
            # Simple traversal of edges to find CONTAINS/IMPORTS
            asset_edges = [e for e in data['graph']['edges'] if e['source'] == asset_id and e['relationship'] in ['CONTAINS', 'IMPORTS']]
            target_ids = [e['target'] for e in asset_edges]
            for node in data['graph']['nodes']:
                if node['id'] in target_ids:
                    cat = node.get('category', 'unknown')
                    lib = node.get('library', 'unknown')
                    api = node.get('api', 'unknown')
                    algo = node.get('algorithm', 'unknown')
                    line = node.get('line', 'unknown')
                    ev = node.get('evidence', 'unknown')
                    evidence_lines.append(f"- **{cat.upper()}** (Line {line}): `{lib}` / `{api}` - Algorithm: `{algo}` - Evidence: *{ev}*")
            
            if evidence_lines:
                for el in evidence_lines:
                    out.write(f"{el}\n")
            else:
                out.write("No direct cryptographic evidence attached (could be a generic file node).\n")
            
            out.write(f"\n#### Assumptions\n\n")
            for asm in asset.get('assumptions', []):
                out.write(f"- {asm}\n")
                
            out.write("\n---\n\n")
