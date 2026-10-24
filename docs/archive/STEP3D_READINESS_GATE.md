# AgileGraph Step 3D / 3D.1 — Final Statistical Readiness Gate and Artifact Reconciliation

**Date:** 2026-10-11  
**Status:** ALL CRITERIA VERIFIED / FIXED AND REVERIFIED  
**Gate Decision:** **PASS — READY TO PROCEED TO INDEPENDENT EXPERT ANNOTATION**  
**Constraint Enforced:** No GATv2 model training conducted; no ground-truth claims made without independent human annotations.

---

## Executive Summary

Step 3D.1 resolves all cross-report and cross-artifact discrepancies identified between Steps 3, 3B, 3C, and 3D. Specifically:
1. **Criticality Count Reconciliation:** Clarifies the exact terminology distinguishing committed files (4,558), eligible files (2,524), file nodes / scored assets (1,432), populated criticality factors (1,338), and uncertain factors (94). Resolves earlier provisional numbers (1,073 populated, 1,520 evaluated) with canonical pipeline numbers.
2. **Repository File Counts & Provenance:** Confirms that all 8 repository HEAD commit SHAs match `benchmark_manifest.json` with 100% byte-for-byte identity. Reconciles `python_cryptography` (true committed file count is **3,072**, correcting a clerical Markdown transcription typo of 3,923). Scanned files match Git tracked files with **0 discrepancies** across all 4,558 files.
3. **Statistical Reporting Rigor:** Preserves explicit undefined correlation handling (`status: UNDEFINED`, `rho: None`) for zero-variance vectors and small samples ($N < 2$), segregating defined ($K=5$) and undefined clusters.

---

## 1. Criticality Count Reconciliation

### A. Terminology Disambiguation
Previous audit drafts exhibited confusion by conflating different stages of the AST and graph extraction pipeline. The canonical definitions are:
- **Committed Files ($4,558$):** Total files tracked in git (`git ls-files`) across the 8 benchmark repositories.
- **Scanned Files ($4,558$):** Files walked and processed by the pipeline runner. Cache directories (`__pycache__`, `.pytest_cache`, `.git`, `.tox`) are pruned, yielding zero untracked file discrepancies.
- **Eligible Language Files ($2,524$):** Files matching supported language extensions (`.py`, `.java`, `.go`, `.pem`, `.crt`, `.key`, `.der`) eligible for AST/crypto parsing.
- **Files with Graph Findings / File Nodes ($1,432$):** Files that produced cryptographic findings (algorithm usage, certificate definitions, or sensitive tokens) and became `file` nodes in the graph.
- **Scored Assets ($1,432$):** In the AgileGraph architecture, risk scores are assigned at the file-asset level. Hence, exactly 1,432 assets are evaluated in `scores`.
- **Populated Criticality Factors ($1,338$):** Assets where the heuristic criticality extractor (`backend/src/risk/criticality.py`) matched a deterministic path heuristic:
  - **Production / Core Crypto Proxy (`0.75`):** $1,079$ assets.
  - **Test / Example Proxy (`0.25`):** $259$ assets.
- **Epistemically Uncertain Criticality (`None`):** $94$ assets that did not contain definitive test or core-crypto path markers (e.g. utility files, build scripts, doc configs). Rather than guessing, the pipeline preserves uncertainty with `value: None`.

### B. Reconciliation of Provisional vs. Canonical Numbers
- **Step 3C (1,073 Populated Assets):** In an earlier intermediate run of Step 3C before leading slash normalization and path regex refinements were completed in `src/risk/criticality.py`, `python_cryptography` populated 997 assets and smaller repos populated 76 assets ($997 + 76 = 1,073$).
- **Step 3D Draft (1,520 Evaluated Assets):** An informal draft had inadvertently summed eligible files from `python_cryptography` ($1,522$) and certificate nodes ($1,076$) into a rough aggregate, creating the figures 470, 988, and 60.
- **Current Canonical Pipeline Output ($1,432$ Evaluated Assets, $1,338$ Populated):**
  - Production (`0.75`): **1,079** (80.6% of populated)
  - Test/Example (`0.25`): **259** (19.4% of populated)
  - Uncertain (`None`): **94** (6.6% of evaluated)
  - Total Scored Assets: $1,079 + 259 + 94 = \mathbf{1,432}$.

### C. Canonical Asset Criticality Table (Direct from Pipeline & `benchmark_summary.json`)

| Repository | Total Scored Assets | Production Proxy (`0.75`) | Test/Example Proxy (`0.25`) | Populated Total | Uncertain (`None`) | Coverage (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `python_itsdangerous` | 7 | 0 | 4 | 4 | 3 | 57.1% |
| `python_bcrypt` | 2 | 0 | 1 | 1 | 1 | 50.0% |
| `python_cryptography` | 1,013 | 895 | 102 | 997 | 16 | 98.4% |
| `java_java_jwt` | 34 | 9 | 25 | 34 | 0 | 100.0% |
| `java_jjwt` | 212 | 171 | 40 | 211 | 1 | 99.5% |
| `go_jwt` | 30 | 0 | 22 | 22 | 8 | 73.3% |
| `go_jwt_go` | 26 | 1 | 18 | 19 | 7 | 73.1% |
| `go_crypto` | 108 | 3 | 47 | 50 | 58 | 46.3% |
| **Corpus Total** | **1,432** | **1,079** | **259** | **1,338** | **94** | **93.4%** |

*Note: Path-based criticality remains explicitly labeled as a heuristic proxy. It is not equivalent to validated operational business impact.*

---

## 2. Reconcile Repository File Counts and Provenance

### A. Commit SHA Provenance Integrity
Every repository in `backend/dataset/corpus` was checked against `benchmark_manifest.json` using `git rev-parse HEAD`. All 8 match the pinned commit SHAs exactly:

| Repository Key | Pinned Commit SHA in Manifest | Local HEAD SHA in `dataset/corpus` | Provenance Verification |
| :--- | :--- | :--- | :--- |
| `python_itsdangerous` | `672971d66a2ef9f85151e53283113f33d642dabd` | `672971d66a2ef9f85151e53283113f33d642dabd` | **EXACT MATCH** |
| `python_bcrypt` | `59b41aaa24c025d1cd231c37d2755b94184a3e67` | `59b41aaa24c025d1cd231c37d2755b94184a3e67` | **EXACT MATCH** |
| `python_cryptography` | `f0ba3000a365d44db153362e847c88339c9231f4` | `f0ba3000a365d44db153362e847c88339c9231f4` | **EXACT MATCH** |
| `java_java_jwt` | `29f252b2d6fea74df6576803d5fce5f6d6799cf3` | `29f252b2d6fea74df6576803d5fce5f6d6799cf3` | **EXACT MATCH** |
| `java_jjwt` | `fb71496164c71442d08adec4571d9616ed5e1b8d` | `fb71496164c71442d08adec4571d9616ed5e1b8d` | **EXACT MATCH** |
| `go_jwt` | `73c870b18e68b6e654b2b03f485aa3c9fab32cea` | `73c870b18e68b6e654b2b03f485aa3c9fab32cea` | **EXACT MATCH** |
| `go_jwt_go` | `9742bd7fca1c67ba2eb793750f56ee3094d1b04f` | `9742bd7fca1c67ba2eb793750f56ee3094d1b04f` | **EXACT MATCH** |
| `go_crypto` | `b39ff6d641ecc5bb4b241737cb0c6b646f3e12a9` | `b39ff6d641ecc5bb4b241737cb0c6b646f3e12a9` | **EXACT MATCH** |

### B. Resolution of `python_cryptography` File Count
- **The Issue:** The Step 3D markdown table listed `python_cryptography` as having 3,923 Git committed files, differing from Step 3C's reported 3,072 files.
- **The Cause:** This was an inadvertent clerical transcription error in the Markdown document table (a calculation artifact where 3,072 + 851 was mistakenly entered).
- **The Ground Truth:** In `backend/dataset/corpus/python_cryptography`, `git ls-files` outputs exactly **3,072 lines**. In `benchmark_summary.json`, `committed_files_git` is recorded as **3,072**, and `scanned_files_walk` is recorded as **3,072**. The regression test `test_file_accounting_zero_untracked_discrepancy` asserts `len(tracked) == 3072` and passes.
- **Artifact Synchronization:** Both `benchmark_manifest.json` and `benchmark_summary.json` were generated from the exact same pinned repository run. The historical raw Step 3 file `backend/dataset/benchmark_step3/benchmark_summary_raw_step3.json` remains preserved unmodified as an audit baseline.

### C. Canonical File Accounting Table Across All 8 Repositories

| Repository | Git Committed Files (`git ls-files`) | Scanned Files (Walk) | Eligible Language Files | Files With Graph Nodes | Eligible Files Without Nodes | Discrepancy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `python_itsdangerous` | 50 | 50 | 15 | 7 | 8 | **0** |
| `python_bcrypt` | 23 | 23 | 5 | 2 | 3 | **0** |
| `python_cryptography` | 3,072 | 3,072 | 1,522 | 1,013 | 509 | **0** |
| `java_java_jwt` | 134 | 134 | 92 | 34 | 58 | **0** |
| `java_jjwt` | 733 | 733 | 455 | 212 | 243 | **0** |
| `go_jwt` | 77 | 77 | 57 | 30 | 27 | **0** |
| `go_jwt_go` | 51 | 51 | 41 | 26 | 15 | **0** |
| `go_crypto` | 418 | 418 | 337 | 108 | 229 | **0** |
| **Total** | **4,558** | **4,558** | **2,524** | **1,432** | **1,092** | **0** |

---

## 3. Undefined Correlation Handling and Statistical Rigor

### Mathematical & Implementation Standard
When either score vector has zero sample variance ($\sigma = 0$), rank correlation is mathematically undefined ($\frac{0}{0}$).
- In `backend/run_benchmark_step3.py`:
  - Returns `"status": "UNDEFINED"`, `"spearman_rho": None`, `"kendall_tau": None`, and explicit `"reason"`.
  - For $N < 2$, returns `"status": "UNDEFINED"` with explicit reason.
  - When true orthogonal correlation occurs ($\sigma > 0, \text{cov} = 0$), returns `"status": "DEFINED"` with `spearman_rho: 0.0`.
- Repository-clustered aggregation segregates defined from undefined clusters:
  - **Defined Repositories ($K=5$):** `python_itsdangerous` ($\rho=1.0$), `python_cryptography` ($\rho=0.5342$), `go_jwt` ($\rho=0.4504$), `go_jwt_go` ($\rho=0.0683$), `go_crypto` ($\rho=0.6894$).
  - **Excluded Undefined Repositories ($K=3$):** 
    - `python_bcrypt` ($N=1 < 2$, undefined sample size).
    - `java_java_jwt` ($N=16$, constant rule baseline vector $0.50$, zero variance).
    - `java_jjwt` ($N=169$, constant rule baseline vector $0.50$, zero variance).
  - Unweighted mean $\rho = 0.5485$; Sample-weighted mean $\rho = 0.5440$; Cluster bootstrap 95% CI $[0.2689, 0.8280]$.
  - Pooled statistics ($N=483$ comparable assets): $\rho = 0.3622$, Kendall $\tau = 0.3053$, paired permutation $p = 0.0001$ ($(0+1)/(10001)$ with finite-sample correction).

---

## 4. Verification Commands and Actual Outputs

### 1. Targeted Regression Suite (17 Tests)
```powershell
pytest -v tests/dataset/test_benchmark_step3.py tests/ml/test_statistical_audit.py tests/risk/test_criticality.py tests/dataset/test_file_accounting.py
```
**Output:**
```
collected 17 items
tests/dataset/test_benchmark_step3.py::test_benchmark_manifest_structure_and_pinned_revisions PASSED [  5%]
tests/dataset/test_benchmark_step3.py::test_benchmark_summary_data_integrity PASSED [ 11%]
tests/dataset/test_benchmark_step3.py::test_rule_based_baseline_reproducibility PASSED [ 17%]
tests/dataset/test_benchmark_step3.py::test_cbomkit_unavailable_contract PASSED [ 23%]
tests/ml/test_statistical_audit.py::test_statistics_constant_rankings_zero_variance PASSED [ 29%]
tests/ml/test_statistical_audit.py::test_statistics_legitimate_zero_correlation PASSED [ 35%]
tests/ml/test_statistical_audit.py::test_statistics_small_sample_size PASSED [ 41%]
tests/ml/test_statistical_audit.py::test_statistics_permutation_finite_sample_correction PASSED [ 47%]
tests/ml/test_statistical_audit.py::test_statistics_tied_rankings_handled PASSED [ 52%]
tests/risk/test_criticality.py::test_criticality_known PASSED            [ 58%]
tests/risk/test_criticality.py::test_criticality_unknown PASSED          [ 64%]
tests/risk/test_criticality.py::test_criticality_path_proxies PASSED     [ 70%]
tests/risk/test_criticality.py::test_criticality_ordinary_utility_remains_uncertain PASSED [ 76%]
tests/risk/test_criticality.py::test_criticality_unintended_category_remains_none PASSED [ 82%]
tests/dataset/test_file_accounting.py::test_file_accounting_zero_untracked_discrepancy PASSED [ 88%]
tests/dataset/test_file_accounting.py::test_cache_directory_pruning_in_runner PASSED [ 94%]
tests/dataset/test_file_accounting.py::test_canonical_benchmark_accounting_and_criticality_reconciliation PASSED [100%]
======================== 17 passed, 1 warning in 4.35s ========================
```

### 2. Full Backend Test Suite (357 Tests)
```powershell
pytest
```
**Output:**
```
================ 353 passed, 4 skipped, 365 warnings in 30.42s ================
```

### 3. Frontend Vitest Suite (19 Tests)
```powershell
npx vitest run
```
**Output:**
```
 Test Files  3 passed (3)
      Tests  19 passed (19)
   Duration  2.63s
```

### 4. Frontend Production Build
```powershell
npm run build
```
**Output:**
```
✓ built in 816ms
dist/index.html                   0.45 kB
dist/assets/index-BtvMrJvh.css   40.01 kB
dist/assets/index-CaxfRlnV.js   532.24 kB
```

---

## 5. Audit Decision Table

| Audit Criterion | Status | Evidence & Resolution |
| :--- | :--- | :--- |
| **Criticality Count Reconciliation** | `FIXED AND REVERIFIED` | Disambiguated files (4,558), eligible (2,524), file nodes / scored assets (1,432), populated criticality (1,338: 1,079 at 0.75, 259 at 0.25), and uncertain (94). Canonical table regenerated directly from pipeline. |
| **Repository File Count & SHA Provenance** | `FIXED AND REVERIFIED` | All 8 repository HEAD SHAs match `benchmark_manifest.json` 100%. Reconciled `python_cryptography` to true 3,072 count (correcting transcription typo of 3,923). Scanned vs. Git files match with 0 discrepancies across all 4,558 files. |
| **Undefined Correlation Segregation** | `VERIFIED` | Zero-variance rankings explicitly return `"status": "UNDEFINED"`, `rho: None`. Excluded from cluster aggregation. Genuine zero correlations distinguished. |
| **Cross-Artifact Reproducibility** | `VERIFIED` | `benchmark_manifest.json` and `benchmark_summary.json` generated from same pinned run. Raw Step 3 backup preserved intact. |
| **Full Regression Verification** | `VERIFIED` | 17 targeted tests passing; 353 backend tests passing; 19 frontend Vitest tests passing; frontend build successful. |

---

## 6. Final Recommendation

### Gate Decision: **PASS — READY TO PROCEED TO INDEPENDENT EXPERT ANNOTATION**
All artifact reconciliation questions have been answered with mathematical and code-level certainty. No GATv2 model training has been conducted, and baseline concordance is strictly characterized as internal heuristic alignment, not empirical risk ground truth.

### Next Step: Expert Annotation Phase
The project is ready to proceed to expert annotation:
1. Develop the structured human annotation rubric for post-quantum cryptographic migration priority.
2. Select stratified asset samples across language, risk factor profiles, and repository clusters.
3. Compute inter-rater agreement (Krippendorff's alpha) on expert annotations before training any graph neural network.
