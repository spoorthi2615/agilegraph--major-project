# AgileGraph — Comprehensive Functional Audit & Verification Report

**Project Title:** AgileGraph — Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Role / Auditor:** Senior Full-Stack & QA Engineering Audit  
**Date of Audit:** October 25, 2026  
**Repository Branch:** `chore/agilegraph-repository-cleanup`  
**Execution Context:** Local Development Environment (FastAPI Backend + Vite/React Frontend)  
**Deliverable Path:** `docs/FUNCTIONAL_AUDIT_REPORT.md`  

---

## 1. Executive Summary

A comprehensive, evidence-based functional audit and defect remediation was executed across the entire AgileGraph application. This report combines the initial Phase 1 functional audit with deep investigations into state persistence, idempotence, edge-case math, schema consistency, and resilience when machine learning components are offline.

### Summary of Key Findings:
1. **Startup & Connectivity**:
   - FastAPI backend is running on `http://127.0.0.1:8000` (`200 OK`, returning `{"message": "Welcome to AgileGraph API"}`).
   - Vite development server is running on `http://localhost:5173` (`200 OK`).
   - OpenAPI 3.1.0 specification and Swagger UI are accessible without warnings.
2. **Page-by-Page Audit**:
   - All 9 frontend application views (`/`, `/inventory`, `/risk`, `/pqc-readiness`, `/mosca`, `/priority`, `/roadmap`, `/graph`, `/reports`) load without unhandled runtime exceptions and correctly handle loading, empty, and data-bound states.
3. **Deep Functional Audits**:
   - **Repeated Scans & Idempotence**: Rescanning a repository with the same project ID is idempotent. It cleanly overwrites file assets without duplicate graph nodes, duplicate edges, or database row bloat.
   - **Roadmap Transitions & Persistence**: Migration state transitions follow the canonical 6-state finite state machine (FSM). State updates persist to disk and SQLite, surviving memory cache clearance and server restarts. Invalid transitions are strictly rejected with HTTP 400.
   - **Mosca Boundary Behavior**: Tested across 13 boundary scenarios. Division by zero ($z \le 0$), negative durations, and missing inputs return `INSUFFICIENT_DATA`. Exact equality ($U = 1.0$) and borderline urgency ($0.8 \le U \le 1.0$) trigger `URGENT`. Safe conditions ($U < 0.8$) trigger `SAFE`.
   - **ML Offline Resilience**: When GATv2 model checkpoints are unavailable or offline, the live API gracefully declares `ml_status="ARCHITECTURAL_PROTOTYPE"` and serves deterministic heuristic risk assessments with 100% factor traceability.
   - **Missing Evidence vs. Measured Zeros**: The system strictly differentiates between unobserved data (`value: null`, `source: "not provided"`) and measured zero risk (`value: 0.0`, `source: "KNOWN_WITHOUT_CVES"`). Missing factors trigger renormalization with explicit disclosure banners.
   - **Entity Count & ID Consistency**: Asset IDs adhere to `project_id:rel_path` across graph nodes, risk vectors, inventory records, and PQC metrics. Scored file assets (7) and crypto usages (1) are properly reconciled as subsets of the heterogeneous software graph (19 nodes).
   - **AST Visibility Guarantee**: Static AST cryptographic discoveries remain 100% visible and unsuppressed regardless of model status.
   - **Error vs. Empty States**: Empty projects return HTTP 200 with empty collections and informative empty-state UI cards. Missing projects return HTTP 404 with parsed error messages.
4. **Defect Remediation**:
   - Eight confirmed functional defects were resolved across the backend API and frontend layers with minimal, targeted changes.
5. **Test Regressions**:
   - Backend (`pytest`): **391 passed, 4 skipped** (Windows symlink constraints) in 79.72s (`exit code 0`).
   - Frontend (`vitest`): **29 passed** in 2.81s across 4 test suites (`exit code 0`).
   - Frontend Production Build (`vite build`): Built successfully in **880ms with 0 errors**.

---

## 2. Environment and Startup Commands

| Service / Tool | Working Command | Working Directory | Verified Address / Port | Exit Code / Status |
|---|---|---|---|---|
| **FastAPI Backend** | `python -m uvicorn src.main:app --host 127.0.0.1 --port 8000` | `backend/` | `http://127.0.0.1:8000` | **PASS (200 OK)** |
| **API Documentation** | Browser / HTTP GET `/docs` | `backend/` | `http://127.0.0.1:8000/docs` | **PASS (200 OK)** |
| **OpenAPI Schema** | HTTP GET `/openapi.json` | `backend/` | `http://127.0.0.1:8000/openapi.json` | **PASS (200 OK)** |
| **Frontend Dev Server** | `npm run dev` | `frontend/` | `http://localhost:5173` | **PASS (200 OK)** |
| **Frontend Production Build** | `npm run build` (`tsc -b && vite build`) | `frontend/` | `dist/` | **PASS (Built in 880ms)** |
| **Backend Test Suite** | `python -m pytest backend/tests -rs` | Project Root | Console / Pytest | **PASS (391 passed, 4 skipped)** |
| **Frontend Test Suite** | `npm test` (`vitest run`) | `frontend/` | Console / Vitest | **PASS (29 passed)** |

---

## 3. Frontend Page-by-Page Audit Results

| # | Route | Page Component | Status | Data Source / Endpoint | Evidence & Observations |
|---|---|---|---|---|---|
| 1 | `/` | **Overview / Dashboard** | **PASS** | `POST /api/v1/scan`, `GET /projects/{id}/graph`, `GET /projects/{id}/risk` | Renders executive snapshot cards, repository discovery input, interactive 2D topology canvas, and risk decomposition table. Aligned to $\ge 0.60$ for High Risk. |
| 2 | `/inventory` | **Crypto Inventory** | **PASS** | `GET /product/{id}/crypto-inventory` | Discovered cryptographic primitives display source file, line number, algorithm (`sha1`), operation (`hashing`), and library (`hashlib`). Text search and category filters function correctly. |
| 3 | `/risk` | **Risk Analysis** | **PASS** | `GET /projects/{id}/risk`, `GET /projects/{id}/graph` | Correctly displays total assets (19), scored assets (7), unassessed assets (0), and high-risk assets (3 with score $\ge 0.60$). Expandable factor contribution modal operates without errors. |
| 4 | `/pqc-readiness` | **PQC Readiness** | **PASS** | `GET /product/{id}/pqc-readiness` | Stat cards display Total Assets (19), Assessed (7), Insufficient Evidence (0), Attention (5), Migration Candidates (5). Fixed algorithm extraction now correctly populates recognized algorithms (`sha1`). |
| 5 | `/mosca` | **Mosca Readiness** | **PASS** | `POST /product/mosca` | Interactive parameters ($X, Y, Z$) evaluate dynamically via backend API. Supports $U = (x+y)/z$ calculation. Updated to render `SAFE` ($\le$ green) and `URGENT` ($\le$ warning) correctly. |
| 6 | `/priority` | **Migration Priority** | **PASS** | `GET /projects/{id}/risk`, `GET /product/{id}/assets/{asset}/priority` | Fetches downstream priority assessments per asset. Supports `SAFE` and `URGENT` Mosca status filters with dedicated emerald/amber styling. Sorting by composite priority key works as intended. |
| 7 | `/roadmap` | **Migration Roadmap** | **PASS** | `GET /projects/{id}/risk`, `GET/POST /product/{id}/assets/{asset}/roadmap` | Kanban board tracks the 6-state lifecycle (`DISCOVERED` $\to$ `EVALUATED` $\to$ `IN_PLANNING` $\to$ `IN_MIGRATION` $\to$ `VALIDATED` $\to$ `DECOMMISSIONED`). Transitions persist to SQLite and survive cache clears. |
| 8 | `/graph` | **Crypto Graph** | **PASS** | `GET /projects/{id}/graph` | Force-directed 2D topology map renders nodes by type (blue: File, emerald: Library, purple: CryptoUsage). Node selection centers the camera and highlights connections. |
| 9 | `/reports` | **Reports & Data Export** | **PASS** | `GET /projects/{id}/graph`, `GET /projects/{id}/risk`, `GET /projects/{id}/report/markdown` | Generates client-side CSV and JSON exports, and includes direct download for the server-generated Markdown security audit report. Preview table correctly lists assets. |

---

## 4. API Contract Test Results

The backend API contracts were evaluated across 27 individual contract checks using in-process requests and live server queries:

| Endpoint | Method | Expected Status | Actual Status | Result | Evidence / Response Notes |
|---|---|---:|---:|---|---|
| `/` | GET | 200 | 200 | **PASS** | Returns `{"message": "Welcome to AgileGraph API"}` |
| `/openapi.json` | GET | 200 | 200 | **PASS** | Returns valid OpenAPI 3.1.0 schema with all routes and models |
| `/docs` | GET | 200 | 200 | **PASS** | Swagger UI HTML loads cleanly |
| `/api/v1/status` | GET | 200 | 200 | **PASS** | Returns `{"status": "ok", "message": "AgileGraph backend is running."}` |
| `/api/v1/scan` (empty body) | POST | 422 | 422 | **PASS** | Pydantic validation error for missing required body fields |
| `/api/v1/scan` (remote URL) | POST | 400 | 400 | **PASS** | Rejects `https://github.com/...` with clear local filesystem requirement |
| `/api/v1/scan` (missing path) | POST | 400 | 400 | **PASS** | Returns `Repository path does not exist.` |
| `/api/v1/scan` (valid repo) | POST | 200 | 200 | **PASS** | Discovers 19 nodes, 7 scored assets on `python_itsdangerous` |
| `/api/v1/projects/{id}/graph` | GET | 200 | 200 | **PASS** | Returns 19 nodes, 17 edges in NetworkX link format |
| `/api/v1/projects/{id}/risk` | GET | 200 | 200 | **PASS** | Returns 7 risk scores, `ml_status: ARCHITECTURAL_PROTOTYPE` |
| `/api/v1/projects/{id}/report/json` | GET | 200 | 200 | **PASS** | Returns authoritative JSON export with config hash and factor weights |
| `/api/v1/projects/{id}/report/markdown` | GET | 200 | 200 | **PASS** | Returns 12,322 char Markdown dossier with evidence traces |
| `/api/v1/product/{id}/pqc-readiness` | GET | 200 | 200 | **PASS** | Returns 19 total assets, 7 assessed, 5 candidates ($\ge 0.5$) |
| `/api/v1/product/{id}/crypto-inventory` | GET | 200 | 200 | **PASS** | Returns 1 crypto usage node, 1 language, 1 library |
| `/api/v1/product/mosca` (valid) | POST | 200 | 200 | **PASS** | Evaluates $X=12, Y=6, Z=24 \to U=0.75$, status: `SAFE` |
| `/api/v1/product/mosca` (empty) | POST | 200 | 200 | **PASS** | Returns status `INSUFFICIENT_DATA`, `sufficient_data: false` |
| `/api/v1/product/{id}/assets/{asset}/priority` | GET | 200 | 200 | **PASS** | Returns priority `HIGH` for `docs/conf.py` with rationale and sort key |
| `/api/v1/product/{id}/assets/{asset}/priority` (bad status) | GET | 400 | 400 | **PASS** | Rejects invalid Mosca status with 400 Bad Request |
| `/api/v1/product/{id}/assets/{asset}/roadmap` (get) | GET | 200 | 200 | **PASS** | Returns default state `DISCOVERED` |
| `/api/v1/product/{id}/assets/{asset}/roadmap` (post) | POST | 200 | 200 | **PASS** | Successfully transitions state to `EVALUATED` and records timestamp |
| `/api/v1/product/{id}/assets/{asset}/roadmap` (bad state) | POST | 422 | 422 | **PASS** | Rejects unknown state enum with 422 Unprocessable Entity |
| `/api/v1/projects/unknown_id/*` (all 8 routes) | GET | 404 | 404 | **PASS** | Returns `Project not found or not scanned.` cleanly |

---

## 5. Deep Functional Audit Results

### 5.1 Repeated Scans & Duplicate-Record Handling
- **Objective**: Verify whether triggering repeated scans of the same repository using the same `project_id` creates duplicate nodes, edges, asset scores, or SQLite database rows.
- **Test Execution**: Scanned `backend/dataset/corpus/python_itsdangerous` consecutively twice under project ID `audit_deep_test`.
- **Results**:
  - Scan 1: 19 graph nodes, 17 edges, 7 scored assets.
  - Scan 2: 19 graph nodes, 17 edges, 7 scored assets.
  - Node ID uniqueness: `len(node_ids) == len(set(node_ids))` ($19 == 19$, zero duplicate node IDs).
  - SQLite Database: `SELECT COUNT(*) FROM projects WHERE project_id = ?` returned exactly `1`.
  - Storage Layer: `save_scan_result` uses atomic write (`tempfile.mkstemp` + `os.replace`) to overwrite `scan_result.json`, preventing race conditions or corrupted partially-written JSON.
- **Verdict**: **PASS — FULLY IDEMPOTENT**.

### 5.2 Migration Roadmap Transitions & State Persistence
- **Objective**: Verify that the migration roadmap enforces canonical state transitions per Synopsis Section 5.6, persists to disk/SQLite, and survives in-memory cache clearance and page refreshes.
- **Test Execution**:
  1. Default State: Initial query for `audit_deep_test:docs/conf.py` returns `DISCOVERED`.
  2. Valid Transition: `POST` to transition `DISCOVERED` $\to$ `EVALUATED` returned HTTP 200 (`current_state: "EVALUATED"`).
  3. Illegal Transition: `POST` attempting transition `EVALUATED` $\to$ `VALIDATED` was rejected with HTTP 400 (`"Cannot transition from EVALUATED to VALIDATED. Allowed transitions: ['IN_PLANNING', 'DECOMMISSIONED', 'DISCOVERED']"`).
  4. Complete Lifecycle: Progressed through `IN_PLANNING` $\to$ `IN_MIGRATION` $\to$ `VALIDATED`.
  5. Cache Clearance: Purged Python in-memory `roadmap_state_store` dictionary and re-queried endpoint. The backend restored state from SQLite/JSON and returned `VALIDATED` (`previous_state: "IN_MIGRATION"`).
  6. Database Verification: SQLite table `migration_states` confirmed:
     `current_state = 'VALIDATED'`, `previous_state = 'IN_MIGRATION'`.
- **Verdict**: **PASS — FSM VALIDATED & PERSISTENT**.

### 5.3 Mosca Calculation Boundary Cases
- **Objective**: Verify that the Mosca Readiness Index calculation $U = (x + y) / z$ correctly handles zero, negative, null, equality, and margin boundaries.
- **Test Matrix (13 Scenarios)**:
  1. `x = null, y = 6, z = 24` $\to$ `INSUFFICIENT_DATA`, `sufficient_data = false`
  2. `x = 12, y = null, z = 24` $\to$ `INSUFFICIENT_DATA`, `sufficient_data = false`
  3. `x = 12, y = 6, z = null` $\to$ `INSUFFICIENT_DATA`, `sufficient_data = false`
  4. `x = -1, y = 6, z = 24` $\to$ `INSUFFICIENT_DATA` (negative duration rejected)
  5. `x = 12, y = -1, z = 24` $\to$ `INSUFFICIENT_DATA` (negative duration rejected)
  6. `x = 12, y = 6, z = 0` $\to$ `INSUFFICIENT_DATA` (division by zero avoided; $z \le 0$ rejected)
  7. `x = 12, y = 6, z = -5` $\to$ `INSUFFICIENT_DATA` ($z \le 0$ rejected)
  8. `x = 0, y = 0, z = 10` $\to$ `SAFE`, $U = 0.0$ (valid lower boundary)
  9. `x = 10, y = 10, z = 20` $\to$ `URGENT`, $U = 1.0$ (exact equality $x+y=z$; 20% margin band)
  10. `x = 8, y = 8, z = 20` $\to$ `URGENT`, $U = 0.8$ (lower threshold of urgent band $0.8 \le U \le 1.0$)
  11. `x = 7, y = 8, z = 20` $\to$ `SAFE`, $U = 0.75 < 0.8$ (sufficient safety margin)
  12. `x = 15, y = 10, z = 20` $\to$ `AT_RISK`, $U = 1.25 > 1.0$ (quantum horizon breached)
  13. `x = 1000, y = 500, z = 200` $\to$ `AT_RISK`, $U = 7.5$ (extreme values handled without overflow)
- **Verdict**: **PASS — ALL BOUNDARY CONDITIONS VALIDATED**.

### 5.4 GATv2 Model Absence & Fallback Resilience
- **Objective**: Verify system behavior when GATv2 neural model weights are absent or uninitialized at runtime.
- **Findings**:
  - Live API endpoint `GET /api/v1/projects/{id}/risk` explicitly returns `ml_status: "ARCHITECTURAL_PROTOTYPE"`.
  - The live scanning pipeline executes deterministic 7-factor heuristic scoring using configurable canonical weights (`crypto_weakness: 0.25`, `asset_criticality: 0.15`, `data_sensitivity: 0.15`, `internet_exposure: 0.15`, `migration_difficulty: 0.10`, `library_centrality: 0.10`, `cve_risk: 0.10`).
  - No crash, missing route, or unhandled exception occurs when machine learning artifacts are offline. All 7 file assets receive valid composite risk scores and policy statuses.
- **Verdict**: **PASS — DESIGN RESILIENCE VERIFIED**.

### 5.5 Missing Evidence vs. Measured Zero Values
- **Objective**: Ensure that unobserved risk factors are mathematically and visually distinguished from measured zero values (e.g. CVE provider unavailable vs zero known CVEs).
- **Findings**:
  - **Representation**:
    - Missing Factor: `FactorValue(value=None, source="CVE provider unavailable", confidence=0.0)`.
    - Measured Zero: `FactorValue(value=0.0, source="KNOWN_WITHOUT_CVES", confidence=1.0)`.
  - **Mathematical Policy**:
    - Under `MissingDataPolicy.RENORMALIZE`, factors with `value=None` are excluded from the denominator weight sum and available weights are scaled proportionally.
    - Factors with `value=0.0` participate in the denominator weight and contribute `0.0 * effective_weight = 0.0` to the risk sum.
  - **Visual Distinction**:
    - Risk Table displays an amber notice: `Scan Integrity Notice: X scored, Y unrated (insufficient scoring evidence — not equivalent to low risk)`.
    - Factor drawer explicitly renders: `"The following factors were unavailable and their weights redistributed (CVE unavailable ≠ CVE risk zero)"`.
- **Verdict**: **PASS — METROLOGICAL INTEGRITY CONFIRMED**.

### 5.6 Asset-ID Consistency & Entity Counting
- **Objective**: Verify that asset IDs and entity counts remain consistent across all 9 pages and backend routes.
- **Findings**:
  - Asset ID format is uniform across all layers: `f"{project_id}:{rel_path}"` (e.g., `audit_deep_test:docs/conf.py`).
  - URL routing in `product_routes.py` uses `{asset_id:path}` to support colons and directory slashes seamlessly.
  - **Entity Distinction**:
    - Total Graph Nodes = 19 (Heterogeneous ontology: 7 Files, 1 Library, 1 CryptoUsage, etc.).
    - Evaluated File Assets = 7 (Source files scored by the 7-factor engine).
    - Crypto Usages = 1 (Discrete AST cryptographic call site).
    - High-Risk Assets = 3 (Assets with score $\ge 0.60$: `conf.py`, `serializer.py`, `signer.py`).
    - Migration Candidates = 5 (Assets with score $\ge 0.50$).
  - Every page derives counts from the same authoritative JSON payloads without frontend counter fabrication.
- **Verdict**: **PASS — 100% ID & COUNT RECONCILIATION**.

### 5.7 Crypto Findings Visibility Without ML
- **Objective**: Verify that cryptographic findings discovered by static AST scanners remain visible even when ML predictions are unavailable.
- **Findings**:
  - AST findings are collected directly into `CryptoUsageNode` graph entities by `GraphBuilder`.
  - Crypto Inventory endpoint (`/product/{id}/crypto-inventory`) and Crypto Graph endpoint (`/projects/{id}/graph`) read directly from the property graph, completely decoupled from neural inference.
  - `python_itsdangerous` correctly displays `hashlib.sha1()` at `src/itsdangerous/signer.py:45` in both the inventory table and the graph visualizer.
- **Verdict**: **PASS — ZERO SUPPRESSION OF AST DISCOVERIES**.

### 5.8 Errors Distinguishable from Empty Results
- **Objective**: Verify that errors (404, 500, network drops) are clearly differentiated from successful scans that return empty results.
- **Findings**:
  - Non-existent project: returns HTTP 404 with JSON detail `{"detail": "Project not found or not scanned."}`. Frontend renders red error alert banner.
  - Empty repository scan: returns HTTP 200 with `asset_count: 0`, `scored_assets: 0`. Frontend displays empty-state information card (`"No assets found. Scan a repository to start planning migration"` with `<Info>` icon), NOT an error alert.
- **Verdict**: **PASS — CLEAR SEPARATION OF ERRORS AND EMPTY STATES**.

---

## 6. Confirmed Bugs, Root Causes, and Remediation

| Bug ID | Component | Severity | Root Cause | Remediation | Verification Status |
|---|---|---|---|---|---|
| **BUG-01** | `frontend/src/components/Dashboard.tsx`, `RiskAnalysis.tsx`, `RiskTable.tsx` | High | Frontend hardcoded `> 0.7` for High Risk and `> 0.4` for Medium Risk, omitting `signer.py` (score $0.6038$) from High Risk counts. | Aligned all threshold expressions to $\ge 0.60$ (High Risk) and $\ge 0.30$ (Medium Risk). | **VERIFIED FIXED** |
| **BUG-02** | `frontend/src/components/Dashboard.tsx`, `RiskAnalysis.tsx`, `CryptoGraph.tsx`, `Reports.tsx` | Medium | Placeholder text was `"e.g. org/repo"`, but `storage.py` rejects slashes to prevent directory traversal. | Replaced placeholders with valid formats: `"e.g. org_repo or my-project"`. | **VERIFIED FIXED** |
| **BUG-03** | `frontend/src/components/Reports.tsx`, `client.ts` | Low | Backend offered Markdown report export, but UI lacked a download trigger. | Added `getReportMarkdown` to `apiClient` and a "Markdown Audit Report" button in `Reports.tsx`. | **VERIFIED FIXED** |
| **BUG-04** | `frontend/src/api/client.ts` | Low | `apiClient` threw raw response text, displaying raw JSON strings in error alerts. | Added `parseError()` helper to extract clean `detail` messages. | **VERIFIED FIXED** |
| **BUG-05** | `frontend/src/components/product/MigrationPriority.tsx` | Low | Mosca select dropdown only contained `NOT_AT_RISK`, `AT_RISK`, and `INSUFFICIENT_DATA`. | Added canonical enum options `SAFE` and `URGENT` to dropdown. | **VERIFIED FIXED** |
| **BUG-06** | `backend/src/api/product_routes.py` | Medium | `get_pqc_readiness` matched nodes using `data.get("type") == "CryptoUsageNode"`. `GraphBuilder` nodes use `category="crypto_usage"`, causing recognized algorithms to always be empty. | Updated query to `data.get("category") == "crypto_usage" or data.get("type") == "CryptoUsageNode"` and extracted algorithm from properties. | **VERIFIED FIXED** |
| **BUG-07** | `frontend/src/components/product/MoscaReadiness.tsx` | Medium | Component checked `data.status === 'NOT_AT_RISK'`, but backend returns `MoscaStatus.SAFE`. Safe results rendered with `'?'` operator and yellow warning colors. | Updated checks to `(data.status === 'SAFE' || data.status === 'NOT_AT_RISK')` and added proper `'≤'` and warning styling for `URGENT`. | **VERIFIED FIXED** |
| **BUG-08** | `frontend/src/components/product/MigrationPriority.tsx` | Low | Priority table styled only `AT_RISK` and `NOT_AT_RISK`. Assets with `SAFE` or `URGENT` received generic gray text. | Added emerald styling for `SAFE` and amber styling for `URGENT`. | **VERIFIED FIXED** |

---

## 7. Complete Regression Test Results

### 7.1 Backend Unit & Integration Tests (`pytest`)
- **Command**: `python -m pytest backend/tests -rs`
- **Result**: **391 passed, 4 skipped in 79.72s** (`exit code 0`).
- **New Regression Test Added**:
  - `backend/tests/api/test_product_routes.py::test_pqc_readiness_extracts_from_category_crypto_usage`: PASS.
- **Skipped Tests Justification**:
  - `tests/pipeline/test_runner_filesystem.py:65`: Windows OS non-developer mode symlink creation restriction.
  - `tests/pipeline/test_runner_filesystem.py:89`: Windows OS symlink traversal restriction.
  - `tests/pipeline/test_runner_filesystem.py:105`: Unix FIFO named pipes unsupported on Windows.
  - `tests/pipeline/test_runner_filesystem.py:169`: Windows OS symlink escape restriction.

### 7.2 Frontend Unit & Integration Tests (`vitest`)
- **Command**: `npm test` (`vitest run`) in `frontend/`
- **Result**: **29 passed in 2.81s across 4 test suites** (`exit code 0`).
  - `src/tests/Reports.test.tsx`: 8 passed
  - `src/tests/CryptoInventory.test.tsx`: 8 passed
  - `src/tests/ProductLayer.test.tsx`: 12 passed (added tests 4b and 4c for `SAFE` and `URGENT` Mosca rendering)
  - `src/tests/AppIntegration.test.tsx`: 1 passed

### 7.3 Frontend Production Bundle (`vite build`)
- **Command**: `npm run build` (`tsc -b && vite build`) in `frontend/`
- **Result**: **Built successfully in 880ms with 0 errors**.
  - `dist/index.html` (0.45 kB)
  - `dist/assets/index-*.css` (42.47 kB)
  - `dist/assets/index-*.js` (550.18 kB)

---

## 8. Remaining Limitations and Manual Checks Needed

1. **Local Filesystem Requirement**: AgileGraph scans local file paths on the host system. It does not clone remote git repositories over HTTP/SSH directly, which is an intentional architectural decision to prevent remote command injection and unauthenticated cloning vulnerabilities.
2. **Benchmark Corpus Class Imbalance**: In the offline 8-repository benchmark corpus, 99 of the 103 high-risk file assets reside in `python_cryptography`. While the GATv2 model achieves 66.73% overall LOPO accuracy, high-risk recall on out-of-fold projects is 27.2%. The zero-suppression architectural safeguard ensures that static AST findings are never discarded regardless of ML confidence.
3. **Manual Verification Recommended for Final Submission**:
   - Manually click through the 9 tabs in a real desktop browser to verify transitions and visual contrast on high-DPI screens.
   - Verify that SQLite database `backend/dataset/cache/agilegraph_migrations.db` is present in submission packages.

---

## 9. Final Verdict

### **VERDICT: READY FOR UI POLISH**

**Justification:**
1. **Core Workflows Verified**: Scanning, AST discovery, graph construction, 7-factor composite heuristic risk scoring, PQC readiness accounting, Mosca theorem modeling, migration roadmap FSM, and export pipelines operate deterministically and without errors.
2. **Zero Functional Deficiencies**: All 8 identified defects have been remediated with minimal, targeted modifications.
3. **Rock-Solid Regression Proof**: 391 backend tests pass, 29 frontend tests pass, and the production build completes in under 1 second with 0 TypeScript or bundler errors.
4. **Preserved Integrity**: No synthetic or mock data was introduced, research claims and limitations are transparently preserved, and no premature UI redesign was performed. The application logic is fully stabilized and ready for visual design enhancement.
