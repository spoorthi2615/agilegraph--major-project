# AgileGraph — Old Deployment vs Current Research Implementation Gap Analysis

## 1. Executive Summary
This report analyzes the gap between the previously deployed AgileGraph application (`https://agilegraph.vercel.app/`), the current local research implementation (`d:\projects\agilegraph new`), and the authoritative project synopsis. 

The analysis reveals a significant divergence: the old deployment demonstrated a highly capable "product" UI containing features (like Mosca readiness, migration planning, comprehensive TLS scanning, and vulnerability enrichment) that are **not** present in the current research-focused repository. The current implementation is strictly constrained to ensure research validity and provenance, focusing on static analysis, dependency manifest parsing, and a heuristic risk engine acting as weak supervision for an unimplemented GATv2 model.

**Crucially, all empirical/expert evaluation features are currently frozen and must not be altered.**

## 2. Current Implementation Status
Based on a direct inspection of the codebase (`README.md`, testing, and build tools):
- **Git SHA**: `baf17a3fdb8c188413ecb0fe55c4447fd6386c57`
- **Working Tree Status**: Dirty (3 modified files, 3 untracked files/dirs).
- **Backend Tests**: 259 passing, 4 skipped (Tested via pytest).
- **Frontend Build Status**: Successful (`tsc -b && vite build` built in 1.74s).

**Implemented Capabilities:**
- Headless CLI scanning with deterministic output.
- AST-based scanning for Python; Regex-based for Java/Go.
- Dependency manifest parsing.
- Graph construction (NetworkX) using the 6-node ontology (though not all nodes are instantiated).
- Basic heuristic risk engine (analyzing factors like crypto weakness and library centrality).
- Dashboard (React) with basic graph-table visualization and explainability.

**Not Implemented / Blocked:**
- Empirical evaluation, GATv2 training, expert annotation import (all currently blocked pending expert validation).
- Mosca visualization, migration-priority tracking, CBOMkit/CVE enrichment, external TLS/CT scanning, Semgrep integration, and Python AES mode detection.

## 3. Old Deployment Feature Inventory
Based on the provided deployment and standard AgileGraph product claims, the old Vercel UI displayed:
- Comprehensive repository scanning and cryptographic asset discovery.
- Advanced crypto graph topology visualizations.
- Detailed risk analysis and prioritization tables.
- Mosca-style readiness indices and PQC migration planning/roadmaps.
- Certificates and TLS configuration scanning (including CT).
- Sensitive-data relationship mapping.
- Rich dashboard reporting and CVE/dependency intelligence overlays.
- Explainability interfaces for graph findings.

## 4. Synopsis Requirement Matrix
| Requirement / Feature | Status |
| :--- | :--- |
| Six node types (File, CryptoUsage, Certificate, Endpoint, Library, SensitiveData) | **PARTIALLY IMPLEMENTED** (Infrastructure exists, but Certificate/Endpoint/SensitiveData not extracted) |
| Seven heuristic factors | **PARTIALLY IMPLEMENTED** (CVE/CBOM, Internet Exposure, Data Sensitivity missing) |
| Python, Java and Go scanning | **IMPLEMENTED** (Python via AST, Java/Go via Regex) |
| Certificates / TLS | **INFRASTRUCTURE ONLY** |
| Dependency manifests | **IMPLEMENTED** |
| NetworkX / Neo4j | **IMPLEMENTED** (NetworkX) |
| GATv2 Architecture | **INFRASTRUCTURE ONLY** (Blocked pending labels) |
| Weak supervision / Heuristic baselines | **IMPLEMENTED** |
| Leakage ablation | **INFRASTRUCTURE ONLY** |
| Bootstrap CI / Significance testing | **BLOCKED / NOT IMPLEMENTED** |
| Expert validation | **INFRASTRUCTURE ONLY** (Pending handoff) |
| Mosca Readiness Index | **NOT IMPLEMENTED** |
| Explainability (GNNExplainer / Attention) | **INFRASTRUCTURE ONLY** (Heuristic explainability exists, but GNN explainer is blocked) |
| Authorized TLS / Passive CT | **NOT IMPLEMENTED** |
| Reproducibility (CLI/Docker) | **IMPLEMENTED** (Docker unverified) |
| Dashboard/Reporting | **PARTIALLY IMPLEMENTED** |

## 5. Old Deployment vs Current Implementation Comparison
**A. UI/product capability shown by the old deployment:**
The old deployment featured advanced PQC migration planning, Mosca readiness scoring, full certificate/TLS analysis, sensitive data mapping, and CVE enrichment.

**B. Functionality actually implemented and backed by the current research code:**
The current implementation only supports basic AST/Regex extraction for CryptoUsages, Files, and Libraries, feeding into a preliminary heuristic engine.

**Conflicts:**
The old UI claimed functionality that simply does not exist in the current research repository. Specifically: Mosca readiness visualization, migration planning tools, certificate/TLS extraction, sensitive-data extraction, and CVE/CBOM enrichment are entirely absent or strictly infrastructure-only in the current backend.

## 6. Research-Validity Gaps
- The GATv2 model, bootstrapping, and empirical metric generation are blocked until authentic expert labels are integrated.
- The current scanners cannot produce the full ontology (missing Certificates, Endpoints, SensitiveData) required for the complete theoretical research model.
- Claimed baseline comparisons against advanced tools (Semgrep, CBOMkit) are not functional.

## 7. Product/UI Gaps
The current frontend is a partial React implementation. It lacks:
- Mosca Readiness Index visualizations.
- Migration-priority tracking and roadmap views.
- Deep dependency intelligence/CVE overlays.
- PQC readiness dashboards present in the old Vercel deployment.

## 8. Features that must not be changed before expert annotation
**DEFERRED UNTIL AFTER EXPERT VALIDATION:**
- Modifying the underlying scanner logic (AST/Regex).
- Changing the risk semantics, heuristic scoring weights, or factor extraction.
- Altering the graph construction ontology or edges.
- Generating empirical results or unblocking the GATv2 training pipeline.

*Reasoning: The project is entering the independent expert-annotation stage using the frozen 165-asset package v1.2.1. Any changes to the scanner or semantics will invalidate the implementation provenance and corrupt the human annotation process.*

## 9. Features safe to implement now
- UI mockups or cosmetic improvements to the React frontend (e.g., bringing back the old dashboard styling), provided they do not require backend data changes.
- Documentation updates.
- Docker environment verification.
- Passive read-only CI/CD pipeline enhancements.

## 10. Post-Expert-Validation Roadmap
- **Phase A**: Complete expert label ingestion and calculate agreement (Kappa).
- **Phase B**: Unblock GATv2 training and empirical evaluation (bootstrapping, significance testing).
- **Phase C**: Implement missing scanner components (Certificates, CT, SensitiveData) and integrate CBOMkit/CVE enrichment.
- **Phase D**: Build out the Mosca Readiness Index, migration planning UI, and final reporting dashboards to achieve parity with the old deployment.

## 11. Final Prioritized Action List

| Requirement / Feature | Old Deployment | Current Implementation | Research Requirement | Status | Priority | When to Implement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Expert validation/ingestion | N/A | Infrastructure Only | Essential | PENDING | P0 | Post-Handoff |
| GATv2 Training & Evaluation | Mocked/Simulated | Infrastructure Only | Essential | BLOCKED | P0 | Phase B |
| Heuristic Engine | Advanced | Basic/Partial | Essential | IMPLEMENTED | P0 | Phase A (Frozen) |
| Python/Java/Go Scanning | Implemented | AST/Regex | Essential | IMPLEMENTED | P0 | Phase A (Frozen) |
| Dashboard (Basic) | Advanced | Basic | Essential | PARTIAL | P1 | Phase B |
| Mosca Readiness Index | Implemented | Not Implemented | Important | NOT IMPLEMENTED | P1 | Phase D |
| Migration Roadmap | Implemented | Not Implemented | Important | NOT IMPLEMENTED | P1 | Phase D |
| CVE / CBOM Enrichment | Implemented | Unavailable | Important | UNAVAILABLE | P2 | Phase C |
| TLS / CT Analysis | Implemented | Auth-gated / Unavailable | Important | NOT IMPLEMENTED | P2 | Phase C |
| Sensitive Data Mapping | Implemented | Not Implemented | Optional/Future | NOT IMPLEMENTED | P2 | Phase C |
| UI/Cosmetic Parity | Excellent | Basic | Optional | DEFERRED | P2 | Phase B |

## Summary Execution Data
- **Current Git SHA**: `baf17a3fdb8c188413ecb0fe55c4447fd6386c57`
- **Working-Tree Status**: Dirty (3 modified files, 3 untracked files/directories)
- **Number of tests currently passing**: 259 passed, 4 skipped
- **Frontend build status**: Success (Vite built client environment for production in 1.74s)
- **Exact report path**: `d:\projects\agilegraph new\AGILEGRAPH_OLD_VS_CURRENT_GAP_ANALYSIS.md`
