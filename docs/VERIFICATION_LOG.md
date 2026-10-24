# AgileGraph — Verification Log (Phase 0)

**Date:** October 24, 2026  
**Git Branch:** `synopsis-alignment`  
**Git Tag:** `pre-synopsis-alignment`  
**Archive Branch:** `archive/expert-annotation` (pinned at HEAD `4914ec4`)  
**Operating System:** Windows (PowerShell)  
**Python Version:** Python 3.13.7  
**Node/Vite Version:** Vite 8.3.2, Vitest 5.0.3, React 19.2.8  

---

## 1. Initial Test and Build Execution Results

### 1.1 Backend Pytest Suite
Command: `pytest` in `backend/`
```
collected 411 items
========== 407 passed, 4 skipped, 1141 warnings in 572.89s (0:09:32) ==========
```
- **Tests Passed:** 407
- **Tests Skipped:** 4 (`tests/scanners/dependencies/test_cve.py` network/mock skips, `tests/pipeline/test_runner_filesystem.py` symlink creation permission skips on Windows)
- **Tests Failed:** 0
- **Total:** 411

### 1.2 Frontend Vitest Suite
Command: `npx vitest run` in `frontend/`
```
 ✓ src/tests/Reports.test.tsx (8 tests) 1361ms
 ✓ src/tests/CryptoInventory.test.tsx (8 tests) 2044ms
 ✓ src/tests/ProductLayer.test.tsx (10 tests) 2008ms
 ✓ src/tests/AppIntegration.test.tsx (1 test) 690ms

 Test Files  4 passed (4)
      Tests  27 passed (27)
   Duration  94.64s
```
- **Test Files Passed:** 4
- **Tests Passed:** 27
- **Tests Failed:** 0

### 1.3 Frontend Production Bundle Build
Command: `npm run build` (`tsc -b && vite build`) in `frontend/`
```
vite v8.3.2 building client environment for production...
transforming...
✓ 2945 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-DJgGwU8h.css   41.74 kB │ gzip:   7.64 kB
dist/assets/index-w_dddNq9.js   548.14 kB │ gzip: 162.16 kB
✓ built in 1.57s
```
- **Build Status:** SUCCESS (0 TypeScript errors, 0 build errors)

---

## 2. Resolution of UNVERIFIED Hypotheses (Section 3 Findings)

| Item | Hypothesis / Problem | Code Inspection Findings & Ground Truth Evidence | Resolution Status |
| :--- | :--- | :--- | :--- |
| **P1** | Contradiction on whether Certificate, Endpoint, SensitiveData nodes are extracted. | Scanners exist and are active: `src/scanners/certificates/scanner.py`, `endpoints/scanner.py`, `sensitive_data/scanner.py`. They are executed in `src/pipeline/runner.py` (lines 87-104) and handled in `src/graph/builder.py`. Tests in `test_six_node_graph.py` and `test_certificate_scanner.py` pass. README was outdated. | **VERIFIED: Scanners ARE implemented and extracting all 3 node types.** |
| **P3** | Mosca/migration/roadmap reported implemented in README but "NOT IMPLEMENTED" in gap analysis. | `src/risk/mosca.py`, `src/risk/migration_priority.py`, `src/models/migration_state.py`, and `src/api/product_routes.py` are fully implemented. Frontend components `MoscaReadiness.tsx`, `MigrationPriority.tsx`, `MigrationRoadmap.tsx`, `PqcReadiness.tsx` are mounted in `App.tsx`. Stale gap analysis reflected pre-`4914ec4` state. | **VERIFIED: Product layer IS implemented; gap analysis was stale.** |
| **P4** | Migration triage uses only 0.80/0.50 thresholds and Mosca AT_RISK; exposure posture and URGENT band unused. | Inspected `src/risk/migration_priority.py` and `src/risk/mosca.py`. `calculate_migration_priority` does NOT accept exposure posture as an input. `MoscaStatus` contains only `AT_RISK`, `NOT_AT_RISK`, `INSUFFICIENT_DATA` (no `URGENT` or `SAFE` bands; no $U = (x+y)/z$ calculation). | **CONFIRMED DEFECT: Requires M3 and F5 alignment with synopsis.** |
| **P5** | Asset criticality: 0.50 shared-utility tier disappeared; 80% assigned 0.75. | Inspected `src/risk/criticality.py` line 28: any file containing "crypto", "auth", "jwt", or "token" received 0.75 before reaching the `in_degree >= 3` check at line 32. Because the benchmark repos are crypto libraries (`python_cryptography`, `jwt`, etc.), nearly all files matched 0.75. | **CONFIRMED DEFECT: Requires M2 tightening to genuine security-critical modules.** |
| **P7** | Graph edges: Schema may mis-model relationships relative to synopsis. | Inspected `src/graph/builder.py`: Line 144 creates `(File)-[:EXPOSES]->(Endpoint)`. Line 53 creates `(File)-[:DEPENDS_ON]->(Library)`. The synopsis requires `Endpoint -[:EXPOSES]-> CryptoUsage`, `File -[:CALLS]-> Endpoint`, and `File -[:IMPORTS]-> Library`. | **CONFIRMED DEFECT: Requires M4 graph schema enforcement.** |
| **P10** | Symlink/non-regular file protection missing beyond cache pruning. | Inspected `src/pipeline/runner.py` lines 49-74: Canonical `os.path.realpath`, `_stat.S_ISREG` checks, and symlink skips (`_stat.S_ISLNK`) are already present. Tests in `tests/pipeline/test_runner_filesystem.py` verify symlink rejection and escape prevention. | **VERIFIED: Security protections ARE implemented and tested.** |
| **P11** | Lifecycle state machine, SQLite storage, transition log, and product endpoints. | Implemented in `src/models/migration_state.py`, `src/core/storage.py`, `src/api/product_routes.py`. Tables for `projects`, `migration_states`, and `migration_transitions` exist with SQLite persistence. Verified by `test_storage.py` and `test_product_routes.py`. | **VERIFIED: Implemented in backend, SQLite database, and product routes.** |
| **API Route List** | Confirm all endpoints required by synopsis exist. | Routes in `src/api/routes.py` and `product_routes.py`: `POST /api/scan`, `GET /api/projects`, `GET /api/graph/{id}`, `GET /api/risk/{id}`, `GET /api/inventory/{id}`, `GET /api/product/pqc-readiness/{id}`, `POST /api/product/mosca/evaluate`, `GET /api/product/migration/priority/{id}`, `GET /api/product/migration/roadmap/{id}`, `POST /api/product/migration/state/transition`. | **VERIFIED: All routes exist and are tested in `test_product_routes.py`.** |
| **Dashboard Views** | Confirm views match synopsis 5.7. | `App.tsx` routes to `/` (Dashboard), `/inventory` (Inventory), `/risk` (Factors/Risk), `/graph` (Force Graph), `/reports` (Reports), `/pqc-readiness` (PQC), `/mosca` (Mosca), `/priority` (Queue), `/roadmap` (Kanban Board). | **VERIFIED: All required views exist in React UI.** |
| **Docker Build** | Check Docker daemon and container build. | `docker --version` returns `29.6.1`. Docker Desktop daemon is not running on host (`pipe/dockerDesktopLinuxEngine: not found`). Marked `UNVERIFIED` in README per instructions. | **VERIFIED: Docker CLI available, daemon inactive, status documented as UNVERIFIED.** |
