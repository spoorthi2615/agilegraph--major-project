# AgileGraph: Graph-Learned Crypto-Agility Risk Scoring

**Research Status:** 
This repository implements the infrastructure for AgileGraph. 
> ⚠️ **IMPORTANT**: The Graph Attention Network (GATv2) and subsequent empirical evaluations are currently **BLOCKED** pending the collection and importation of expert labels. The current system outputs **HEURISTIC ANALYSIS** intended to act as weak supervision and structural priors. It does not output empirical ML results.

## Overview

AgileGraph translates cryptographic footprints into asset-level migration priorities for Post-Quantum Cryptography (PQC) transitions. It employs static analysis, a six-node ontology, and a heuristic risk engine that structures raw source-code artifacts into a meaningful post-quantum risk topology.

## Architecture

1. **Scanners**: Extract ASTs, dependency manifests, and endpoint definitions (Python, Java, Go).
2. **Graph Construction**: Constructs a NetworkX graph based on the six-node ontology: `file`, `library`, `crypto_usage`, `endpoint`, `data_flow`, `configuration`. Relationships like `IMPORTS`, `CONTAINS`, `CALLS`, etc. connect these nodes.
3. **Heuristic Risk Engine**: Evaluates seven factors (e.g., `crypto_weakness`, `library_centrality`, `migration_difficulty`) using a renormalized weighting system (handling unavailable contexts like CVE risk).
4. **Dashboard**: A React application offering interactive visualization, graph-table interaction, and explainability.

## Reproducibility & CLI

AgileGraph is reproducible using the built-in command-line interface.

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

## Testing

The backend suite tests the logic of the heuristic engine, the schema constraints, and the CLI execution without fabricating empirical evidence.
```bash
cd backend
python -m pytest tests/
```

Continuous Integration (CI) is configured via GitHub Actions in `.github/workflows/ci.yml`.

## Current Status and Limitations

- **Implemented**: CLI, Dashboard, Heuristic Risk Engine, Scanners (Python, Java, Go), Reproducible Container (Dockerfile), Graph Ontology.
- **Pending/Blocked**: Genuine expert annotation import, GATv2 training, Statistical validation (Kappa, F1), Leakage-ablation results.

*AgileGraph is designed to ensure rigorous provenance and structural determinism before proceeding to expert-in-the-loop evaluation.*
