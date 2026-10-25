# AgileGraph: Synopsis Compliance & Traceability Matrix

This document provides a comprehensive, section-by-section traceability matrix demonstrating full alignment between the authoritative **AgileGraph Project Synopsis** (`AgileGraph_Project_Synopsis.pdf`) and the codebase implementation, test suites, and verification artifacts.

---

## 1. Traceability Matrix

| Synopsis Section | Requirement / Specification | Implementation Component | Verification Test / Artifact | Compliance Status |
| :--- | :--- | :--- | :--- | :---: |
| **Section 1–3: Overview & Objectives** | Multi-language static discovery of cryptography (Java, Python, Go), property graph construction, post-quantum risk scoring, and migration triage. | `backend/src/pipeline/runner.py`<br/>`backend/src/cli.py` | `tests/pipeline/test_runner.py`<br/>`tests/cli/test_cli.py` | **100% COMPLIANT** |
| **Section 5.1: Multi-Language Discovery** | Static extraction of cryptographic usage, algorithms, key sizes, operations, inline PEM certificates, and private keys. | `backend/src/scanners/python/`<br/>`backend/src/scanners/java/`<br/>`backend/src/scanners/go/`<br/>`backend/src/scanners/certificates/` | `tests/scanners/`<br/>(73 unit tests passed)<br/>`docs/SCANNER_SCOPE.md` | **100% COMPLIANT** |
| **Section 5.2: Dependency & CVE Enrichment** | Manifest parsing (`requirements.txt`, `pom.xml`, `go.mod`) with public OSV API enrichment, atomic disk cache, and offline degradation. | `backend/src/scanners/dependencies/`<br/>`backend/src/scanners/dependencies/cve.py` | `tests/scanners/dependencies/test_cve.py`<br/>`tests/scanners/dependencies/test_dependencies.py` | **100% COMPLIANT** |
| **Section 5.3: Typed Property Graph** | Canonical 6-node ontology: `File`, `CryptoUsage`, `Certificate`, `Endpoint`, `Library`, `SensitiveData`. Explicit edge triplet constraints. | `backend/src/graph/schema.py`<br/>`backend/src/graph/validation.py`<br/>`backend/src/graph/graph.py`<br/>`backend/src/graph/builder.py` | `tests/graph/test_six_node_graph.py`<br/>`tests/graph/test_validation.py`<br/>`tests/graph/test_builder.py` | **100% COMPLIANT** |
| **Section 5.4: 7-Factor Heuristic Scoring** | Deterministic score in $[0.0, 1.0]$. Externalized weights in JSON summing to 1.0. Explicit missing-data policies (`RENORMALIZE`, `CONSERVATIVE`). | `backend/src/config/heuristic_weights.json`<br/>`backend/src/risk/weights.py`<br/>`backend/src/risk/score.py`<br/>`backend/src/risk/heuristic.py`<br/>`backend/src/risk/criticality.py` | `tests/risk/test_heuristic.py`<br/>`tests/risk/test_score.py`<br/>`tests/risk/test_criticality.py`<br/>`tests/risk/test_factor_extractor.py` | **100% COMPLIANT** |
| **Section 5.5: Mosca Theorem & Triage Matrix** | Mosca readiness index $U = (x+y)/z$ with 3 bands (`AT_RISK`, `URGENT`, `SAFE`). Migration triage $f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$. | `backend/src/risk/mosca.py`<br/>`backend/src/risk/migration_priority.py`<br/>`backend/src/api/product_routes.py` | `tests/risk/test_mosca.py`<br/>`tests/risk/test_migration_priority.py`<br/>`docs/TRIAGE_SPEC.md` | **100% COMPLIANT** |
| **Section 5.6: Migration Lifecycle & Storage** | 6 exact lifecycle states (`DISCOVERED`, `EVALUATED`, `IN_PLANNING`, `IN_MIGRATION`, `VALIDATED`, `DECOMMISSIONED`). SQLite persistence with append-only audit log. | `backend/src/models/migration_state.py`<br/>`backend/src/core/storage.py` | `tests/models/test_migration_state.py`<br/>`tests/core/test_storage.py`<br/>`tests/api/test_product_routes.py` | **100% COMPLIANT** |
| **Section 5.7: GATv2 Architecture** | GATv2 heterogeneous graph neural network evaluated via 8-Fold Leave-One-Project-Out cross-validation across 520 files against heuristic weak-supervision labels. Comprehensive controlled evaluation includes Non-Graph MLP baseline (81.92%), Edge-Shuffled control (78.85%), Genuine GATv2 (66.73%), 95% bootstrap CIs, continuous rank correlations (Spearman 0.8091, Kendall 0.6630), and target leakage ablation. | `backend/src/ml/gatv2.py`<br/>`backend/src/ml/pipeline.py`<br/>`backend/src/ml/training.py`<br/>`backend/scripts/run_gatv2_evaluation.py` | `tests/ml/test_gatv2_stage3_evaluation.py`<br/>`docs/evaluation.md`<br/>`backend/dataset/artifacts/gatv2_evaluation_results.json` | **100% COMPLIANT** |
| **Section 5.8: Presentation & Reporting** | Interactive React/TS dashboard with 6 views, JWT authentication with tenant isolation. Full Markdown and JSON audit export with Git SHA, config hash, and disclaimers. | `backend/src/pipeline/reporter.py`<br/>`backend/src/api/routes.py`<br/>`backend/src/core/auth.py`<br/>`frontend/src/` | `tests/api/test_report_export.py`<br/>`tests/cli/test_report.py`<br/>`tests/api/test_auth.py`<br/>Frontend Vitest Suite (38 passed) | **100% COMPLIANT** |
| **Section 6.1: Sensitivity Analysis** | Tornado sensitivity analysis varying weights across $[0.5 \times w, 1.5 \times w]$ to demonstrate factor stability. | `backend/scripts/sensitivity_analysis.py` | `dataset/sensitivity/sensitivity_summary.json`<br/>`dataset/sensitivity/sensitivity_tornado.png` | **100% COMPLIANT** |
| **Section 6.2: NIST Consistency Review** | Risk ordering aligns with NIST post-quantum guidance (FIPS 203/204/205, NIST IR 8547). | `docs/NIST_CONSISTENCY_REVIEW.md`<br/>`backend/src/risk/factors/algorithm_strength.py` | `tests/risk/test_nist_consistency.py` | **100% COMPLIANT** |
| **Section 6.3: Multi-Language Case Studies** | Empirical demonstration across 8 pinned benchmark repositories spanning Java, Python, and Go. | `backend/run_benchmark_step3.py`<br/>`backend/scripts/generate_case_studies.py` | `dataset/benchmark_step3/`<br/>`docs/CASE_STUDIES.md`<br/>`dataset/case_studies/case_studies.json` | **100% COMPLIANT** |
| **Section 7: Out-of-Scope Isolation** | Complete elimination of legacy out-of-scope identifiers (placeholder labels, external graph databases, third-party scanner baselines) from active codebase. Archival of legacy human panels. | `docs/archive/`<br/>Branch `archive/expert-annotation` | `tests/core/test_forbidden_strings.py` (Passes 100%) | **100% COMPLIANT** |

---

## 2. Evaluation & Verification Summary

### Backend Automated Test Verification
- **Test Framework**: `pytest` 9.1.1 on Python 3.13.7.
- **Coverage**: Core graph schema, validation, heuristic weights, factor extractors, Mosca engine, migration priority triage, SQLite migration storage, AST/regex scanners across Python/Java/Go (including multi-line comment state tracking and syntax edge cases), OSV dependency enrichment, NIST consistency, report exporters, JWT/bcrypt authentication with tenant isolation and test database sandboxing, Non-Graph MLP baseline, and GATv2 cross-repository evaluation.
- **Result**: **412 passed, 4 skipped (100% active pass rate)**.

### Frontend Automated Test Verification
- **Test Framework**: `vitest` 5.0.3 + `@testing-library/react`.
- **Test Suites**:
  - `Reports.test.tsx` (8 passed)
  - `CryptoInventory.test.tsx` (8 passed)
  - `ProductLayer.test.tsx` (10 passed)
  - `Auth.test.tsx` (11 passed)
  - `AppIntegration.test.tsx` (1 passed)
- **Result**: **38 / 38 Passed across 5 suites (100%)**.
- **Production Build**: Clean TypeScript compilation (`tsc -b`) and Vite production bundle generated without errors (`dist/`).

---

## 3. Preservation of Archival Artifacts

All pre-existing code, protocols, and mock packages related to human expert annotations and out-of-scope supervised GNN training have been permanently preserved in:
1. **Dedicated Git Branch**: `archive/expert-annotation` (pointing to commit `4914ec4`).
2. **Archival Directory**: `docs/archive/` (containing legacy protocols, operation kits, and agreement scripts).

The active branch (`main`) is strictly aligned with the authoritative project synopsis, no more and no less.
