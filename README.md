# AgileGraph: Graph-Learned Crypto-Agility Risk Scoring

**Research Status:** 
This repository implements the infrastructure for AgileGraph. 
> ⚠️ **IMPORTANT**: The Graph Attention Network (GATv2) is currently **BLOCKED / PENDING_EXPERT_LABELS** pending the collection and importation of expert labels. **Empirical evaluation = BLOCKED**. The current system outputs **HEURISTIC ANALYSIS** intended to act as weak supervision and structural priors. It does not output empirical ML results. No fabricated empirical metrics, expert counts, kappa, F1, accuracy, p-values, confidence intervals, or GATv2 performance are claimed.

## Overview

AgileGraph translates cryptographic footprints into asset-level migration priorities for Post-Quantum Cryptography (PQC) transitions. It employs static analysis, a six-node ontology, and a heuristic risk engine that structures raw source-code artifacts into a meaningful post-quantum risk topology.

## Architecture

1. **Scanners** (`IMPLEMENTED` / `PARTIALLY IMPLEMENTED` / `INFRASTRUCTURE ONLY`): 
   - Language AST extraction (Python, Java, Go) is `IMPLEMENTED`.
   - Dependency manifest parsing is `IMPLEMENTED`. However, CVE/CBOM enrichment is not currently available through CBOMkit (`UNAVAILABLE`). Unavailable CVE information remains missing/unavailable; unavailable CVE information is NOT interpreted as zero risk.
   - Certificate/TLS scanning infrastructure exists (`INFRASTRUCTURE ONLY`). Active external TLS scanning is authorization-gated. Current TLS functionality has only been verified against the permitted/local development scenario, and broad Internet TLS coverage has not been empirically demonstrated.
2. **Graph Construction** (`IMPLEMENTED`): Constructs a NetworkX graph based on the authoritative six-node ontology: `File`, `CryptoUsage`, `Certificate`, `Endpoint`, `Library`, `SensitiveData`. 
   *Note: The ontology supports six node types, but the current real corpus does not necessarily instantiate every category. The absence of observed instances must not be represented as evidence that the scanner discovered those categories.*
3. **Heuristic Risk Engine** (`IMPLEMENTED`): Evaluates a subset of seven factors (e.g., `crypto_weakness`, `library_centrality`). The score is preliminary as multiple metadata pipelines (e.g., data sensitivity, internet exposure, cve risk) remain unimplemented. Unavailable contexts are renormalized.
4. **Dashboard** (`PARTIALLY IMPLEMENTED`): A React application offering interactive visualization, graph-table interaction, and explainability. Note: the Mosca network view and the migration-priority/risk-reduction planning interfaces promised in the synopsis are currently **NOT IMPLEMENTED**.

## Reproducibility & CLI

AgileGraph is reproducible using the built-in command-line interface.

- **Deterministic CLI behavior**: `VERIFIED` (Repeated scans of the same local input were verified to be byte-for-byte identical).
- **Docker packaging**: `IMPLEMENTED` (Dockerfile provided).
- **Docker build/execution**: `UNVERIFIED` (Docker build/execution has not been verified in the current development environment).

### Running a Scan

To run a headless heuristic scan on a target repository:

```bash
cd backend
python -m src.cli scan /path/to/repo --output report.json --project-id my-project
```

### Generating an Audit Report

To generate a human-readable Markdown report from the JSON scan output:

```bash
cd backend
python -m src.cli report report.json --output audit_report.md
```

The CLI explicitly states the boundaries of the analysis and preserves all traceability down to the scanned files.

## Dashboard Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173`. 

## Testing (`TESTED`)

The backend suite tests the logic of the heuristic engine, the schema constraints, and the CLI execution without fabricating empirical evidence.
```bash
cd backend
python -m pytest tests/
```

Continuous Integration (CI) is configured via GitHub Actions in `.github/workflows/ci.yml`.

## Current Status and Limitations

- **IMPLEMENTED**: CLI, Dashboard, Heuristic Risk Engine, Scanners (AST Python/Java/Go), Graph Ontology, Dependency Manifest Parsing.
- **TESTED**: Backend test suite, CLI commands, Frontend build.
- **PARTIALLY IMPLEMENTED**: Dependency intelligence (CVE/CBOM is unavailable).
- **INFRASTRUCTURE ONLY**: Certificate/TLS Scanner, GATv2 architecture, leakage ablation, baseline comparison, expert validation schema.
- **UNAVAILABLE / NOT INCLUDED**: 
  - CBOMkit/CVE enrichment (unavailable).
  - Semgrep (not utilized in the current scanner implementation).
  - CT (Certificate Transparency) / passive certificates (not implemented).
  - Certificate, Endpoint, and SensitiveData nodes (ontology supports them, but current scanners do not extract them).
  - Mosca visualization and migration-priority tracking interfaces are not implemented in the frontend.
- **SCANNER LIMITATIONS**:
  - Scanner recall is limited to recognized AST patterns. Known misses exist in Java (e.g., `Mac`, `KeyFactory`, `KeyAgreement`, `SecureRandom`) and Go (e.g., HMAC, standard `RSA/ECDSA` usage outside specific generator patterns). 
  - Coverage claims are restricted strictly to "within the evaluated AST API patterns", not comprehensive cryptographic discovery.
- **PENDING**: Genuine expert annotation import.
- **BLOCKED**: GATv2 training, Empirical evaluation, Statistical inference.

*AgileGraph is designed to ensure rigorous provenance and structural determinism before proceeding to expert-in-the-loop evaluation.*
