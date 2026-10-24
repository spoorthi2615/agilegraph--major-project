# AgileGraph Step 3C — Statistical and Reproducibility Audit Report

**Date of Audit:** October 11, 2026  
**Audit Scope:** Public Repository Benchmark, Baseline Statistical Calculations, Asset Criticality Proxies, Mixed-Crypto Risk Understatement, and Provenance Reproducibility.  
**Execution Environment:** Windows, Python 3.13.7, PyTorch Geometric, Vitest 5.0.3, Vite 8.3.2.  
**Supervised Model Training Status:** **FROZEN / NOT STARTED**. No GATv2 training was performed. No predictive validity claims are made.

---

## 1. Repository File Counts Reconciliation

### Discrepancy Investigation
In Step 3, the report stated 4,801 scanned regular files vs. 4,558 Git-committed files. In Step 3B, after initial filtering, 4,568 non-Git files were counted, leaving a **10-file discrepancy** relative to the 4,558 committed files tracked by `git ls-files`.

An automated inspection of all 8 repository working trees revealed the exact identity and origin of all 10 additional files:
- **`python_itsdangerous` (6 files):**
  - `tests/test_itsdangerous/__pycache__/__init__.cpython-313.pyc`
  - `tests/test_itsdangerous/__pycache__/test_encoding.cpython-313-pytest-9.1.1.pyc`
  - `tests/test_itsdangerous/__pycache__/test_serializer.cpython-313-pytest-9.1.1.pyc`
  - `tests/test_itsdangerous/__pycache__/test_signer.cpython-313-pytest-9.1.1.pyc`
  - `tests/test_itsdangerous/__pycache__/test_timed.cpython-313-pytest-9.1.1.pyc`
  - `tests/test_itsdangerous/__pycache__/test_url_safe.cpython-313-pytest-9.1.1.pyc`
- **`python_bcrypt` (1 file):**
  - `tests/__pycache__/test_bcrypt.cpython-313-pytest-9.1.1.pyc`
- **`python_cryptography` (3 files):**
  - `tests/__pycache__/__init__.cpython-313.pyc`
  - `tests/__pycache__/conftest.cpython-313-pytest-9.1.1.pyc`
  - `tests/__pycache__/utils.cpython-313.pyc`

**Root Cause:** These 10 files were transient CPython bytecode (`.pyc`) cache files generated inside `__pycache__` directories during previous pytest test executions.  
**Fix Implemented:** 
1. All transient `.pyc` files were deleted from the cached corpus.
2. `backend/src/pipeline/runner.py` was updated so that `os.walk` explicitly prunes `dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', '.pytest_cache', '.tox', '.mypy_cache')]`.
3. Added unit tests in `tests/dataset/test_file_accounting.py` guaranteeing 0 discrepancy between `git ls-files` and non-cache source files.

### Exact File Accounting Table (Post-Pruning)

| Repository Key | Committed Git Files (`git ls-files`) | Excluded by Extension Rules (docs, yaml, images) | Eligible Source Files (`.py`, `.java`, `.go`, certs, manifests) | Actual Files Scanned (non-git walk) | Files Producing Graph Nodes | Eligible Files Without Findings | Discrepancy (Scanned vs. Git) |
|---|---|---|---|---|---|---|---|
| `python_itsdangerous` | 50 | 35 | 15 | 50 | 7 | 8 | **0** |
| `python_bcrypt` | 23 | 18 | 5 | 23 | 2 | 3 | **0** |
| `python_cryptography` | 3,072 | 1,986 | 1,086 | 3,072 | 1,013 | 73 | **0** |
| `java_java_jwt` | 134 | 42 | 92 | 134 | 34 | 58 | **0** |
| `java_jjwt` | 733 | 278 | 455 | 733 | 212 | 243 | **0** |
| `go_jwt` | 77 | 20 | 57 | 77 | 30 | 27 | **0** |
| `go_jwt_go` | 51 | 10 | 41 | 51 | 26 | 15 | **0** |
| `go_crypto` | 418 | 81 | 337 | 418 | 108 | 229 | **0** |
| **Corpus Total** | **4,558** | **2,470** | **2,088** | **4,558** | **1,432** | **656** | **0** |

---

## 2. Statistical Methodology Audit

### 2.1 Aggregation Method: Pooled vs. Repository-Clustered
- **Pooled Comparable Assets ($N=483$):**  
  Concatenates paired scores $(s_{\text{heuristic}, i}, s_{\text{rule}, i})$ across all repositories into a single vector.  
  *Rationale:* Evaluates the global prioritization queue across an entire application security inventory.
  - Spearman $\rho = 0.3613$ ($p < 10^{-6}$)
  - Kendall $\tau = 0.3045$ ($p < 10^{-6}$)
  - 95% Bootstrap CI: `[0.2886, 0.4268]`
- **Repository-Clustered Aggregation (across 7 repositories with $N \ge 3$):**  
  Computes correlation within each repository individually, then averages across repositories. This accounts for intra-repository non-independence:
  - **Unweighted Mean Spearman $\rho$:** `0.3918`
  - **Sample-Weighted Mean Spearman $\rho$:** `0.3352`
  - **Clustered Bootstrap 95% CI (1,000 repository-level resamples):** `[0.1180, 0.6775]`

### 2.2 Handling of Edge Cases
- **Ties:** Computed via fractional/mid-rank assignment (`scipy.stats.spearmanr` and `kendalltau`), which prevents rank inflation from identical score values.
- **Zero Variance / Constant Rankings:** When an asset vector has $\sigma = 0$, rank correlation is mathematically undefined. `compute_baseline_statistics` catches this explicitly, returning $\rho = 0.0, p = 1.0$ and records a descriptive explanation rather than throwing `ZeroDivisionError` or propagating `NaN`.
- **Small Sample Sizes:** Repositories with $N < 2$ (e.g. `python_bcrypt`, $N=1$) return `None` with an explanatory note. Repositories with $N=3$ (e.g. `python_itsdangerous`) are computed but flagged with broad confidence intervals.

### 2.3 Permutation Test Rigor & Finite-Sample Correction
- **Null Hypothesis ($H_0$):** $E[s_{\text{heuristic}} - s_{\text{rule}}] = 0$ under paired sign exchangeability (the two scoring systems produce identical expected risk values for the same assets).
- **Test Statistic:** $T = |\bar{D}|$ where $D_i = s_{\text{heuristic}, i} - s_{\text{rule}, i}$.
- **Permutations:** $B = 10,000$ paired sign flips.
- **Finite-Sample Correction:** Previous runs reported $p = 0.0$ when 0 permutations exceeded $T_{\text{obs}}$. A finite permutation test can never produce a true zero p-value. We implemented the standard Davison & Hinkley (1997) / Phipson & Smyth (2010) correction:
  $$p = \frac{\sum_{b=1}^B I(|T_b| \ge |T_{\text{obs}}|) + 1}{B + 1}$$
  For $B=10,000$ with 0 extreme outcomes, the minimum empirical p-value is strictly reported as $p = \frac{0 + 1}{10001} \approx 0.0001$.
- **Interpretation Safeguard:** This paired permutation test assesses whether the score distributions between the two systems are statistically distinguishable ($p = 0.0001$). **It does NOT indicate ranking superiority or accuracy**, which requires independent ground-truth labels.

### 2.4 NDCG and CBOMkit Integrity
- **NDCG@k:** Formally marked **`NOT_AVAILABLE`**. Graded relevance labels require expert human security annotations. Presenting NDCG using heuristic or rule-based outputs as pseudo-labels would constitute circular confirmation bias.
- **CBOMkit:** Formally marked **`UNAVAILABLE`**. CBOMkit is not installed in this environment; no synthetic comparisons were fabricated.

---

## 3. Asset Criticality Validation

Path-based inference is a **heuristic proxy** and must never be misrepresented as verified business or organizational criticality.

### Validated Behavior Across Representative Categories

| Asset Role | Example Path | Inferred Criticality | Factor Confidence | Source Designation |
|---|---|---|---|---|
| **Explicit Metadata** | Any asset with `business_criticality: "CRITICAL"` | `1.00` | 1.0 | `explicit metadata` |
| **Security Module Proxy** | `src/crypto/aes_engine.py`, `auth/jwt.go` | `0.75` | 0.8 | `inferred security-critical module proxy: {path}` |
| **Shared Dependency Proxy** | `src/common/core.py` (with in-degree $\ge 3$) | `0.50` | 0.7 | `inferred shared dependency module proxy (in-degree={N})` |
| **Test & Example Proxy** | `tests/test_signer.py`, `examples/basic.py` | `0.25` | 0.9 | `inferred non-production asset (test/example proxy)` |
| **Ordinary Utility File** | `src/utils/text_formatter.py` (in-degree < 3) | `None` | 0.0 | `not provided` (Preserved as uncertain) |
| **Non-File Asset** | `library`, `endpoint` nodes | `None` | 0.0 | `not provided` (Unintended categories remain None) |

### Value Distribution Across the Benchmark Corpus (1,073 populated assets)
- `0.75` (Security module proxy): 73 assets (auth/crypto/token implementations).
- `0.50` (Shared module proxy): 12 assets (modules with in-degree $\ge 3$).
- `0.25` (Test & example proxy): 988 assets (unit/integration test fixtures).
- `None` (Uncertain / ordinary utility): 359 assets (retained as unrated for this factor).

---

## 4. Reassessment of Mixed-Crypto Scoring

### Understatement Risk Analysis
When an asset contains both recognized cryptographic primitives (e.g. SHA-256 with weakness 0.1) and unrecognized algorithms (e.g. an unclassified proprietary cipher):
- If the unknown algorithm is silently ignored, the asset receives a low risk score of 0.1, understating the potential vulnerability of the unreviewed cipher.
- Reviewers inspecting the score without the audit trail would mistake the asset for purely modern, vetted cryptography.

### Systematic Comparison of Three Policies

| Policy | Mechanism | Score on (SHA-256 + Unknown) | Confidence | Audit Trail Visibility | Trade-offs & Limitations |
|---|---|---|---|---|---|
| **1. Naive Filtering (Historical)** | Ignores unrecognized algorithms; evaluates recognized algorithms only. | `0.10` | 0.90 | Loses unknown algorithm evidence. | Understates risk; masks unclassified algorithms. |
| **2. Evidence-Preserving with Uncertainty Discount (Active)** | Takes recognized risk, discounts confidence ($0.90 \rightarrow 0.65$), appends unrated algorithm names to source. | `0.10` | 0.65 | `algorithm classification (sha256) [unrated crypto also detected: custom_cipher]` | Preserves recognized ordering while highlighting epistemic uncertainty to human reviewers. |
| **3. Conservative Floor (Alternative Option)** | Imposes a minimum risk floor ($0.50$) whenever an unknown algorithm is present. | `0.50` | 0.65 | Explicit floor applied. | Pessimistic bound; shifts scores upward for assets that might only have benign custom utilities. |

**Decision:** Policy 2 was adopted as the active policy in [`FactorExtractor.extract`](file:///d:/projects/agilegraph%20new/backend/src/risk/factor_extractor.py), with regression tests added in `tests/risk/test_mixed_crypto_audit.py`. Policy 3 is documented and tested as a configurable risk-averse alternative.

---

## 5. Decision & Verification Table

| Audit Criterion | Classification | Evidence & Verification Reference |
|---|---|---|
| **File Accounting Reconciliation** | **FIXED AND REVERIFIED** | Eliminated 10 transient `.pyc` files. Pruned `__pycache__` in `runner.py`. Confirmed exact match: 4,558 Git files == 4,558 scanned files across all 8 repos. Verified via `tests/dataset/test_file_accounting.py`. |
| **Pooled vs. Clustered Statistics** | **VERIFIED** | Reported both pooled ($\rho = 0.3613$, 95% CI `[0.2886, 0.4268]`) and repository-clustered stats (weighted mean $\rho = 0.3352$, 95% CI `[0.1180, 0.6775]`). |
| **Permutation Test Finite-Sample Correction** | **FIXED AND REVERIFIED** | Implemented $(k+1)/(B+1)$ correction. Finite-sample p-value reported as $p = 0.0001$ rather than exact zero. Verified via `tests/ml/test_statistical_audit.py`. |
| **Statistical Edge Cases (Ties, Zero Variance)** | **FIXED AND REVERIFIED** | Mid-rank tie handling verified; zero-variance vectors caught gracefully without runtime exceptions. Verified via `tests/ml/test_statistical_audit.py`. |
| **Asset Criticality Proxies** | **FIXED AND REVERIFIED** | Added example/sample non-production handling (`0.25`), verified ordinary utility uncertainty (`None`), and confirmed non-file categories do not receive values. Verified via `tests/risk/test_criticality.py`. |
| **Mixed-Crypto Scoring Reassessment** | **FIXED AND REVERIFIED** | Evidence preservation and confidence discounting ($0.65$) validated across 5 synthetic cases in `tests/risk/test_mixed_crypto_audit.py`. |
| **Provenance & Reproducibility** | **VERIFIED** | All 8 repository SHAs verified against upstream commits; summary regenerated via `python run_benchmark_step3.py`. Raw Step 3 backup preserved at `benchmark_summary_raw_step3.json`. |
| **Regression Suite Pass** | **VERIFIED** | Backend `pytest`: **351 passed**, 4 skipped. Frontend Vitest: **19 passed**, 0 failed. Frontend Build: **0 errors**. |

---

## 6. Exact Test Commands and Results

### 1. File Accounting & Cache Pruning Regression Tests
```powershell
pytest tests/dataset/test_file_accounting.py
```
**Output:**
```text
============================= test session starts =============================
collected 2 items
tests\dataset\test_file_accounting.py ..                                 [100%]
============================== 2 passed in 1.15s ==============================
```

### 2. Statistical Edge Cases & Finite-Sample Correction Tests
```powershell
pytest tests/ml/test_statistical_audit.py
```
**Output:**
```text
============================= test session starts =============================
collected 4 items
tests\ml\test_statistical_audit.py ....                                  [100%]
============================== 4 passed in 0.45s ==============================
```

### 3. Mixed-Crypto Scoring Audit Tests
```powershell
pytest tests/risk/test_mixed_crypto_audit.py
```
**Output:**
```text
============================= test session starts =============================
collected 5 items
tests\risk\test_mixed_crypto_audit.py .....                              [100%]
============================== 5 passed in 0.47s ==============================
```

### 4. Asset Criticality Proxy & Edge Case Tests
```powershell
pytest tests/risk/test_criticality.py
```
**Output:**
```text
============================= test session starts =============================
collected 5 items
tests\risk\test_criticality.py .....                                     [100%]
============================== 5 passed in 0.14s ==============================
```

### 5. Full Backend Regression Suite
```powershell
pytest
```
**Output:**
```text
============================== 351 passed, 4 skipped, 365 warnings in 32.34s ==============================
```

### 6. Full Frontend Vitest Suite
```powershell
npx vitest run
```
**Output:**
```text
 ✓ src/tests/CryptoInventory.test.tsx (8 tests) 426ms
 ✓ src/tests/ProductLayer.test.tsx (10 tests) 441ms
 ✓ src/tests/AppIntegration.test.tsx (1 test) 417ms
Test Files  3 passed (3)
     Tests  19 passed (19)
```

### 7. Frontend Production TypeScript Compilation
```powershell
npm run build
```
**Output:**
```text
> tsc -b && vite build
✓ 2944 modules transformed.
✓ built in 1.24s
```

---

## 7. Remaining Blockers for Future Modeling
1. **Supervised Labels Required for GATv2:** Model training, supervised ranking metrics (NDCG, MAP), and predictive evaluation cannot proceed without external, verified ground-truth annotations from human security experts.
2. **CBOMkit Integration:** Remains unavailable until the external binary/tool is packaged and installed.
