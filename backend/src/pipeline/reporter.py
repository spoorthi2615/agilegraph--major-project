import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

SCANNER_SCOPE = {
    "python": "AST-based extraction of hashlib, cryptography, Crypto, ssl, urllib",
    "java": "Pattern matching for MessageDigest, Cipher, KeyPairGenerator, Signature, KeyFactory, SecureRandom, jjwt, auth0",
    "go": "AST & regex pattern matching for crypto/md5, sha1, des, aes, rsa, ecdsa, ed25519, elliptic, tls, golang-jwt",
    "dependencies": "Manifest parsing (requirements.txt, pom.xml, go.mod) with OSV API enrichment",
    "certificates": "Inline PEM certificate and private key block discovery",
    "endpoints": "Network endpoint and URL references (http://, https://)",
    "sensitive_data": "Variable name and string heuristic matching for passwords, secrets, tokens, keys"
}

DISCLAIMER = (
    "All risk scores and migration priorities represent operational estimates based on static heuristic rules. "
    "No claims of statistical predictive validity, probability of quantum compromise, or empirical ground truth are made."
)

def get_config_hash() -> str:
    weights_path = Path(__file__).resolve().parents[1] / "config" / "heuristic_weights.json"
    if weights_path.exists():
        with open(weights_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    return "default-weights"

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
        out.write(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        # PROVENANCE & CONFIGURATION METADATA
        out.write(f"## Provenance & Verification Metadata\n\n")
        git_sha = data['provenance'].get('commit_sha') or data['provenance'].get('git_sha') or 'unversioned_working_tree'
        out.write(f"- **Git SHA**: `{git_sha}`\n")
        out.write(f"- **Config Hash (SHA-256)**: `{get_config_hash()}`\n")
        out.write(f"- **Missing Data Policy**: `{data['missing_data_policy']}`\n")
        out.write(f"- **OSV Enrichment Date**: `{data['provenance'].get('osv_enrichment_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))}`\n")
        out.write(f"- **Tool Version**: `agilegraph-v1.0`\n\n")

        # MANDATORY OPERATIONAL ESTIMATE DISCLAIMER
        out.write(f"> **Operational Estimate Disclaimer**: {DISCLAIMER}\n\n")

        # RESEARCH STATUS (MANDATORY)
        out.write(f"## ⚠️ RESEARCH STATUS & INTEGRITY GATE\n\n")
        out.write(f"This report presents a **{data['analysis_type']} ANALYSIS** generated through static code scanning and rule-based priors. It is designed for operational review.\n\n")
        out.write(f"- **GATv2**: `ARCHITECTURAL_PROTOTYPE`\n")
        out.write(f"- **Validation status**: `{data.get('expert_validation_status', 'HEURISTIC_DETERMINISTIC')}`\n")
        out.write(f"- **Empirical evaluation**: `{data['ml_status']}`\n\n")
        out.write(f"> **Important**: No fabricated empirical metrics, kappa scores, F1/accuracy results, or p-values are claimed in this report.\n\n")
        
        # SCANNER SCOPE DECLARATIONS
        out.write(f"## Declared Scanner Scope\n\n")
        for lang, scope_desc in SCANNER_SCOPE.items():
            out.write(f"- **{lang.capitalize()}**: {scope_desc}\n")
        out.write("\n")

        # SCAN SUMMARY
        out.write(f"## Scan Summary\n\n")
        out.write(f"- **Scanned Files**: {data['provenance'].get('scanned_files', 0)}\n")
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


def build_export_payload(project_id: str, data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs an authoritative JSON export payload containing full provenance metadata,
    configuration hash, active factor weights, scanner scope, missing-data policy,
    OSV enrichment date, and the mandatory operational estimate disclaimer.
    """
    prov = data_dict.get("provenance", {})
    scores = data_dict.get("scores", [])
    g = data_dict.get("graph")
    nodes_count = len(g.nodes) if g is not None else 0
    edges_count = len(g.edges) if g is not None else 0

    weights_path = Path(__file__).resolve().parents[1] / "config" / "heuristic_weights.json"
    weights_dict = {}
    if weights_path.exists():
        try:
            with open(weights_path, "r", encoding="utf-8") as f:
                weights_dict = json.load(f).get("weights", {})
        except Exception:
            pass

    return {
        "report_metadata": {
            "project_id": project_id,
            "tool_version": "agilegraph-v1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": prov.get("commit_sha") or prov.get("git_sha") or "unversioned_working_tree",
            "config_hash": get_config_hash(),
            "missing_evidence_policy": data_dict.get("missing_data_policy", "RENORMALIZE"),
            "osv_enrichment_date": prov.get("osv_enrichment_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "operational_disclaimer": DISCLAIMER,
            "ml_status": "ARCHITECTURAL_PROTOTYPE",
            "evaluation_status": "DETERMINISTIC_HEURISTIC"
        },
        "scanner_scope": SCANNER_SCOPE,
        "factor_weights": weights_dict,
        "graph_summary": {
            "total_nodes": nodes_count,
            "total_edges": edges_count,
            "evaluated_assets": len(scores)
        },
        "assets": scores
    }
