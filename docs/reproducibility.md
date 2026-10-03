# AgileGraph Reproducibility Guide

This document describes how to build and run the AgileGraph heuristic scanner deterministically using the containerized CLI.

**IMPORTANT:** This represents *reproducibility infrastructure*. Final end-to-end reproducibility requires the locked expert dataset and empirical model evaluation, which are currently BLOCKED pending expert annotations.

## 1. Prerequisites

- Docker installed
- Git installed

## 2. Container Build

To guarantee a stable execution environment, AgileGraph is packaged in a Docker container based on `python:3.13-slim`.

```bash
cd /path/to/agilegraph
docker build -t agilegraph-cli .
```

## 3. Running the Pipeline

The CLI allows you to execute the exact same scanning, graph-building, and risk-scoring pipeline that runs in the AgileGraph dashboard.

To scan a local repository (e.g., your current working directory), mount it into the container and execute the `scan` command:

```bash
docker run --rm -v $(pwd):/workspace -v $(pwd)/out:/out agilegraph-cli scan /workspace --output /out/report.json --project-id my-project
```

### Options

- `repository`: The absolute path to the directory inside the container to scan.
- `--output`: The absolute path where the JSON report should be written.
- `--project-id`: A unique identifier for the scan.
- `--missing-data-policy`: How to handle missing context (e.g. unavailable CVE data). Options are `STRICT` or `RENORMALIZE`. Defaults to `RENORMALIZE`.

## 4. Output Inspection

The CLI outputs a structured JSON report. 

**Integrity Constraints:**
- `analysis_type` is hardcoded to `HEURISTIC`.
- `ml_status` and `expert_validation_status` are hardcoded to `BLOCKED`.
- The report includes `provenance` metadata to link the heuristic results directly to the scanned files.

Example inspection:

```json
{
  "project_id": "my-project",
  "analysis_type": "HEURISTIC",
  "ml_status": "BLOCKED",
  "expert_validation_status": "BLOCKED",
  "missing_data_policy": "RENORMALIZE",
  "provenance": {
    "scanned_files": 42,
    "is_mock": false
  },
  "assets": [
    {
      "asset_id": "/workspace/main.py",
      "score": 0.428,
      "scale": "0.0-1.0",
      "factors": {...},
      "weights": {...},
      "weighted_contributions": {...},
      "missing_factors": ["cve_risk"]
    }
  ],
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

## 5. Determinism Constraints

The scanning and heuristic generation pipeline is deterministic with respect to the input source code. 
Repeated scans of the same pinned inputs will produce equivalent graphs, nodes, factor extractions, and heuristic scores.

*Note:* File system timestamps and directory traversal order may vary depending on the host OS. This may cause the order of the nodes in the JSON array to differ, but the substantive structural mapping and cryptographic vulnerability factors remain deterministic.
