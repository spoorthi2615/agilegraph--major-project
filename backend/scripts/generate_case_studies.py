"""
AgileGraph Representative Case Study Generator.

Extracts 3-5 diverse, concrete case studies across scanned repositories illustrating:
  1. High Shor-vulnerable asymmetric crypto with external endpoint exposure.
  2. Classically broken hash (MD5/SHA1) legacy usage.
  3. High-centrality shared cryptographic utility.
  4. Quantum-resilient symmetric cipher with contained exposure.

Outputs:
  - docs/CASE_STUDIES.md
  - dataset/case_studies/case_studies.json
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))

from src.pipeline.runner import run_pipeline
from src.risk.mosca import MoscaStatus
from src.risk.migration_priority import calculate_migration_priority

OUTPUT_DIR = "dataset/case_studies"
DOCS_OUT = "../docs/CASE_STUDIES.md"
CORPUS_ROOT = "dataset/corpus"


def generate_case_studies():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Representative case study assets curated from benchmark scans
    # Note: Repository names, file paths, and algorithms correspond to actual scanned assets.
    # Numerical factor scores and Mosca planning parameters (x, y, z) are illustrative scenario
    # assumptions demonstrating downstream triage across distinct risk archetypes, not dynamically
    # queried pipeline extractions or empirical ground-truth measurements.
    case_studies = [
        {
            "case_id": "CASE-01",
            "title": "Shor-Vulnerable RSA Key Generation in Public Service",
            "repository": "python_cryptography",
            "asset_id": "python_cryptography:src/cryptography/hazmat/primitives/asymmetric/rsa.py",
            "archetype": "High Quantum Vulnerability + External Exposure",
            "data_status": "ILLUSTRATIVE_SCENARIO_ASSUMPTION",
            "data_provenance": "Scanned repository asset archetype; numerical factor values and Mosca parameters are illustrative scenario assumptions.",
            "narrative": (
                "Direct RSA asymmetric private key generation. Under Shor's algorithm on a CRQC, "
                "integer factorization is solved in polynomial time O((log N)^3). "
                "Combined with exposure to calling endpoints, this represents critical migration urgency."
            ),
            "algorithm": "rsa",
            "operation": "key_generation",
            "key_size": 2048,
            "exposure_posture": "INTERNET_FACING",
            "mosca_planning": "AT_RISK (x=36, y=24, z=36 -> U=1.67)",
            "base_risk": 0.88,
            "factors": {
                "crypto_weakness": {"value": 0.90, "rationale": "RSA-2048 Shor-vulnerable"},
                "data_sensitivity": {"value": 0.80, "rationale": "Private key material"},
                "asset_criticality": {"value": 0.75, "rationale": "Security core implementation"},
                "internet_exposure": {"value": 1.00, "rationale": "Binds external interface"},
                "cve_risk": {"value": 0.10, "rationale": "Clean dependency baseline"},
                "library_centrality": {"value": 0.45, "rationale": "Imported across modules"},
                "migration_difficulty": {"value": 0.70, "rationale": "Stateful key exchange replacement"}
            },
            "priority": "HIGH",
            "triage_rationale": "High Priority: Critical preliminary risk (0.88) combined with AT_RISK planning urgency and INTERNET_FACING exposure."
        },
        {
            "case_id": "CASE-02",
            "title": "Legacy Broken MD5 Checksum Construction",
            "repository": "python_itsdangerous",
            "asset_id": "python_itsdangerous:src/itsdangerous/signer.py",
            "archetype": "Classically Broken Hash Function",
            "data_status": "ILLUSTRATIVE_SCENARIO_ASSUMPTION",
            "data_provenance": "Scanned repository asset archetype; numerical factor values and Mosca parameters are illustrative scenario assumptions.",
            "narrative": (
                "MD5 cryptographic hash utilized in legacy message signing. MD5 is classically broken "
                "via practical collision attacks (Wang et al.) and disallowed under NIST SP 800-131A. "
                "Must be deprecated regardless of quantum timeline."
            ),
            "algorithm": "md5",
            "operation": "hashing",
            "key_size": None,
            "exposure_posture": "INTERNAL",
            "mosca_planning": "URGENT (x=12, y=12, z=30 -> U=0.80)",
            "base_risk": 0.79,
            "factors": {
                "crypto_weakness": {"value": 1.00, "rationale": "MD5 classically broken collision resistance"},
                "data_sensitivity": {"value": 0.60, "rationale": "Session token signature"},
                "asset_criticality": {"value": 0.75, "rationale": "Token serialization core"},
                "internet_exposure": {"value": 0.20, "rationale": "Internal helper module"},
                "cve_risk": {"value": 0.00, "rationale": "No published CVEs"},
                "library_centrality": {"value": 0.60, "rationale": "Directly called by API handlers"},
                "migration_difficulty": {"value": 0.30, "rationale": "Drop-in replacement with SHA-256"}
            },
            "priority": "HIGH",
            "triage_rationale": "High Priority: Preliminary risk is critical (0.79) due to broken hash primitive (MD5)."
        },
        {
            "case_id": "CASE-03",
            "title": "High-Centrality Shared Cryptographic Utility Library",
            "repository": "go_crypto",
            "asset_id": "go_crypto:ssh/common.go",
            "archetype": "High Centrality Architectural Dependency",
            "data_status": "ILLUSTRATIVE_SCENARIO_ASSUMPTION",
            "data_provenance": "Scanned repository asset archetype; numerical factor values and Mosca parameters are illustrative scenario assumptions.",
            "narrative": (
                "Shared SSH transport negotiation module with in-degree >= 12 across the repository. "
                "High centrality amplifies blast radius; migration requires coordinated protocol upgrades."
            ),
            "algorithm": "ecdsa",
            "operation": "signature",
            "key_size": 256,
            "exposure_posture": "INTERNET_FACING",
            "mosca_planning": "URGENT (x=24, y=12, z=40 -> U=0.90)",
            "base_risk": 0.81,
            "factors": {
                "crypto_weakness": {"value": 0.90, "rationale": "ECDSA P-256 Shor-vulnerable"},
                "data_sensitivity": {"value": 0.75, "rationale": "SSH transport credentials"},
                "asset_criticality": {"value": 0.75, "rationale": "Security transport core"},
                "internet_exposure": {"value": 1.00, "rationale": "Network listener exposed"},
                "cve_risk": {"value": 0.20, "rationale": "Low dependency risk"},
                "library_centrality": {"value": 0.85, "rationale": "High in-degree architectural hub"},
                "migration_difficulty": {"value": 0.80, "rationale": "Protocol-level wire format changes"}
            },
            "priority": "HIGH",
            "triage_rationale": "High Priority: High preliminary risk (0.81), high centrality (0.85), and external exposure."
        },
        {
            "case_id": "CASE-04",
            "title": "Quantum-Resilient Modern Symmetric Cipher (AES-256-GCM)",
            "repository": "java_jjwt",
            "asset_id": "java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/AesGcmKeyAlgorithm.java",
            "archetype": "Quantum-Resilient Symmetric Encryption",
            "data_status": "ILLUSTRATIVE_SCENARIO_ASSUMPTION",
            "data_provenance": "Scanned repository asset archetype; numerical factor values and Mosca parameters are illustrative scenario assumptions.",
            "narrative": (
                "Modern AES-256 authenticated encryption in Galois/Counter Mode. Under Grover's algorithm, "
                "effective key search complexity is 2^128, which strictly satisfies NIST/CNSA 2.0 post-quantum requirements."
            ),
            "algorithm": "aes",
            "operation": "encryption",
            "key_size": 256,
            "exposure_posture": "INTERNAL",
            "mosca_planning": "SAFE (x=12, y=6, z=60 -> U=0.30)",
            "base_risk": 0.32,
            "factors": {
                "crypto_weakness": {"value": 0.10, "rationale": "AES-256 resilient to Grover (128-bit quantum margin)"},
                "data_sensitivity": {"value": 0.50, "rationale": "Encrypted payload data"},
                "asset_criticality": {"value": 0.50, "rationale": "Shared encryption utility"},
                "internet_exposure": {"value": 0.20, "rationale": "Internal helper library"},
                "cve_risk": {"value": 0.00, "rationale": "Zero CVE vulnerabilities"},
                "library_centrality": {"value": 0.40, "rationale": "Standard module usage"},
                "migration_difficulty": {"value": 0.20, "rationale": "Compliant modern primitive"}
            },
            "priority": "LOW",
            "triage_rationale": "Low Priority: Low base risk (0.32) and SAFE planning horizon (U=0.30)."
        }
    ]

    # Save JSON artifact
    json_path = os.path.join(OUTPUT_DIR, "case_studies.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(case_studies, f, indent=2)

    # Save Markdown report
    md_content = generate_markdown_report(case_studies)
    with open(DOCS_OUT, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Case studies generated successfully:")
    print(f"  Structured JSON: {json_path}")
    print(f"  Markdown Report: {DOCS_OUT}")


def generate_markdown_report(cases: List[Dict[str, Any]]) -> str:
    lines = [
        "# AgileGraph Architectural Case Studies",
        "",
        "> [!IMPORTANT]",
        "> **Scope & Methodological Note:**",
        "> These case studies illustrate AgileGraph's property-graph discovery, heuristic factor weighting, and migration triage logic across four representative cryptographic archetypes drawn from the pinned benchmark repositories.",
        "> The repository names, file paths, and cryptographic algorithms represent actual open-source components scanned in the benchmark corpus.",
        "> **The numerical factor scores, composite risk scores, and Mosca planning horizons ($x, y, z$) are illustrative scenario assumptions** designed to exercise the triage decision matrix across distinct operational risk profiles.",
        "> They are **not dynamically generated pipeline extractions or empirically validated ground-truth measurements**.",
        "",
        "---",
        ""
    ]

    for c in cases:
        lines.extend([
            f"## {c['case_id']}: {c['title']}",
            "",
            f"- **Archetype**: {c['archetype']}",
            f"- **Repository**: `{c['repository']}`",
            f"- **Asset Identifier**: `{c['asset_id']}`",
            f"- **Algorithm / Primitive**: `{c['algorithm'].upper()}` ({c['operation']})",
            f"- **Network Exposure**: `{c['exposure_posture']}`",
            f"- **Mosca Readiness Assumption**: `{c['mosca_planning']}` *(Illustrative planning parameters)*",
            f"- **Base Heuristic Risk Score**: **{c['base_risk']:.2f}** / 1.00 *(Illustrative scenario score)*",
            f"- **Migration Triage Priority**: **`{c['priority']}`**",
            f"- **Data Status**: *Illustrative scenario assumption (not dynamically generated pipeline output)*",
            "",
            "### Architectural Context & Narrative",
            c["narrative"],
            "",
            "### Factor Breakdown (Illustrative Scenario)",
            "| Factor | Value | Rationale |",
            "| :--- | :---: | :--- |"
        ])
        for fname, fdict in c["factors"].items():
            lines.append(f"| `{fname}` | `{fdict['value']:.2f}` | {fdict['rationale']} |")
        
        lines.extend([
            "",
            f"**Triage Rationale**: {c['triage_rationale']}",
            "",
            "---",
            ""
        ])

    return "\n".join(lines)


if __name__ == "__main__":
    generate_case_studies()
