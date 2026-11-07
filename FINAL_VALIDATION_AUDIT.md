# AgileGraph: Final Four-Expert Validation Audit, Statistical Verification & Research Documentation

**Project**: AgileGraph – Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Institutional Affiliation**: Final-Year B.Tech Major Project, Department of Computer Science and Engineering (Cyber Security), NMAM Institute of Technology (NMAMIT), Nitte  
**Guide**: Ms. Madhushree  
**Student Investigators**: Spoorthi (`NNM23CB058`), Sindhoora R (`NNM23CB057`), Nivedita V Shetty (`NNM23CB033`), Sujan S (`NNM23CB062`)  
**Audit Date**: November 7, 2026  
**Audit Status**: **VERIFIED & ACCEPTED (Zero Discrepancy)**  

---

## 1. Executive Summary & Audit Verdict

This audit document provides a comprehensive, research-grade statistical verification and integrity review of the four-expert validation study conducted for **AgileGraph**. The validation panel comprised four independent cybersecurity practitioners evaluating a corpus of **160 repository-scoped cryptographic source-code assets** sampled across 8 open-source software repositories (Go, Java, Python).

### Key Audit Findings:
1. **Mathematical Reproducibility**: Every reported metric—including all 6 pairwise linear weighted Cohen's Kappas, multi-rater Fleiss' Kappa, adjudicated consensus distributions, heuristic Macro-F1, and percentile bootstrap confidence intervals—has been independently verified down to four decimal places directly from raw submission workbooks.
2. **Asset Identity Integrity**: Asset keys are rigorously repository-scoped (`repository_name:relative_file_path`). The 9 repeated filenames between `go_jwt` and `go_jwt_go` (e.g., `ecdsa.go`, `hmac.go`, `rsa.go`) are preserved as 18 distinct source files, completely preventing cross-repository asset collision.
3. **Rigorous Handling of Incomplete Cases**: Reviewer 4 abstained from 6 assets citing *"Insufficient context"*. These missing values were not imputed; instead, multi-rater Fleiss' Kappa was evaluated strictly on the $N = 154$ mutually rated assets ($\kappa_{\text{Fleiss}} = 0.7791$), while consensus for the remaining 6 assets was adjudicated across the 3 participating raters (2 unanimous, 4 majority).
4. **Data Segregation & Anti-Leakage Invariant**: Expert annotations are strictly segregated from machine learning training routines. PyTorch GATv2 training (`backend/src/ml/gatv2.py`, `train.py`) has zero access to expert labels, preventing circular validation.
5. **Defensible Scientific Divergence**: The moderate concordance between human experts and AgileGraph's 7-factor heuristic engine ($\text{Macro-F1} = 0.3225$, $\text{Weighted } \kappa = 0.2625$) reflects a fundamental domain distinction: human experts classify primarily by *intrinsic cryptographic exploitability* (Shor/Grover vulnerability of public-key ciphers), whereas AgileGraph's multi-factor engine dampens risk for test fixtures, unexposed internal helpers, and library wrappers through reachability and exposure modeling.

---

## 2. Quantitative Audit: Reported vs. Independently Recalculated Values

| Metric | Original Reported Value | Independently Recalculated Value | Discrepancy | Audit Status |
| :--- | :---: | :---: | :---: | :---: |
| **Total Canonical Assets** | 160 | **160** | 0 | **VERIFIED** |
| **Participating Expert Reviewers** | 4 | **4** | 0 | **VERIFIED** |
| **Mutually Rated Assets (All 4 Experts)**| 154 | **154** | 0 | **VERIFIED** |
| **Reviewer 4 Abstentions ("Insufficient context")** | 6 | **6** | 0 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 1 vs Exp 2** ($N=160$) | 0.6697 | **0.6697** (0.669654) | 0.0000 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 1 vs Exp 3** ($N=160$) | 0.7611 | **0.7611** (0.761131) | 0.0000 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 1 vs Exp 4** ($N=154$) | 0.6928 | **0.6928** (0.692761) | 0.0000 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 2 vs Exp 3** ($N=160$) | 0.8994 | **0.8994** (0.899361) | 0.0000 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 2 vs Exp 4** ($N=154$) | 0.9917 | **0.9917** (0.991745) | 0.0000 | **VERIFIED** |
| **Pairwise $\kappa_{\text{linear}}$: Exp 3 vs Exp 4** ($N=154$) | 0.8855 | **0.8855** (0.885490) | 0.0000 | **VERIFIED** |
| **Arithmetic Mean Pairwise Linear Kappa** | 0.8167 | **0.8167** (0.816690) | 0.0000 | **VERIFIED** |
| **Multi-Rater Fleiss' Kappa** ($N=154$) | 0.7791 | **0.7791** (0.779100) | 0.0000 | **VERIFIED** |
| **Adjudicated Consensus HIGH** | 80 | **80** (50.0%) | 0 | **VERIFIED** |
| **Adjudicated Consensus MEDIUM** | 51 | **51** (31.9%) | 0 | **VERIFIED** |
| **Adjudicated Consensus LOW** | 29 | **29** (18.1%) | 0 | **VERIFIED** |
| **Unanimous Consensus Cases** | 117 | **117** (73.1%) | 0 | **VERIFIED** |
| **Majority Consensus Cases** | 32 | **32** (20.0%) | 0 | **VERIFIED** |
| **Resolved 2-vs-2 Ties** | 11 | **11** (6.9%) | 0 | **VERIFIED** |
| **Heuristic Macro-F1 vs Consensus** | 0.3225 | **0.3225** | 0.0000 | **VERIFIED** |
| **Heuristic 95% Bootstrap CI** ($B=1000$) | [0.2558, 0.3799] | **[0.2558, 0.3799]** | 0.0000 | **VERIFIED** |
| **Weighted Cohen's Kappa vs Heuristic** | 0.2625 | **0.2625** | 0.0000 | **VERIFIED** |
| **Backend Tests Passing** | 429 passed, 4 skipped | **429 passed, 4 skipped** | 0 | **VERIFIED** |
| **Frontend Tests Passing** | 39 passed | **39 passed** | 0 | **VERIFIED** |

---

## 3. Phase 1: Repository & Submission File Ingestion Audit

### 3.1 Raw Submission File Provenance
Submissions were collected using the standardized reviewer workbook (`AgileGraph_Review_Sheet.xlsx`) containing two worksheets: `Reviewer Profile & Rubric` and `Asset Review (160)`. The raw files are stored in `backend/dataset/expert_annotations/submissions/`:

| File Name | Size (Bytes) | Valid Rows | Abstentions | File Status |
| :--- | :---: | :---: | :---: | :--- |
| `AgileGraph_Review_Sheet_completed.xlsx` (Exp 1) | 19,346 | 160 | 0 | Preserved Unaltered |
| `AgileGraph_Review_Sheet_Completed -2.xlsx` (Exp 2) | 20,534 | 160 | 0 | Preserved Unaltered |
| `AgileGraph_Review_Sheet_Completed -3.xlsx` (Exp 3) | 17,979 | 160 | 0 | Preserved Unaltered |
| `AgileGraph_Filled - 4.xlsx` (Exp 4) | 16,151 | 154 | 6 | Preserved Unaltered |

### 3.2 Canonical Asset Identity & Deduplication Resolution
Early pipelines experienced an asset-identity bug where raw filenames were used as keys, collapsing 160 assets to 151. Investigation confirmed that exactly 9 filenames exist in both `go_jwt` and `go_jwt_go`:
1. `ecdsa.go`
2. `example_test.go`
3. `hmac.go`
4. `hmac_example_test.go`
5. `hmac_test.go`
6. `rsa.go`
7. `rsa_pss.go`
8. `rsa_pss_test.go`
9. `rsa_test.go`

**Audited Correction**: The canonical asset identity is strictly constructed as `f"{repo}:{file_path}"`. This guarantees that `go_jwt:ecdsa.go` and `go_jwt_go:ecdsa.go` are treated as distinct cryptographic source assets across parsing, deduplication, consensus adjudication, and graph matching.

---

## 4. Phase 2: Inter-Annotator Agreement Verification

### 4.1 Pairwise Agreement Across All $\binom{4}{2} = 6$ Reviewer Pairs
Linear weighted Cohen's Kappa assigns penalties proportional to ordinal class distance ($|i - j|$), quadratic weighting penalizes distance squared ($(i - j)^2$), and unweighted measures strict exact agreement:

| Pair Index | Reviewer Comparison | Mutually Rated Items | Linear Weighted $\kappa$ | Quadratic Weighted $\kappa$ | Unweighted $\kappa$ | Interpretation |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | **Expert 1 vs Expert 2** | 160 | **0.6697** | 0.7405 | 0.5945 | Substantial Agreement |
| 2 | **Expert 1 vs Expert 3** | 160 | **0.7611** | 0.8219 | 0.6937 | Substantial Agreement |
| 3 | **Expert 1 vs Expert 4** | 154 | **0.6928** | 0.7724 | 0.6085 | Substantial Agreement |
| 4 | **Expert 2 vs Expert 3** | 160 | **0.8994** | 0.9088 | 0.8907 | Near-Perfect Agreement |
| 5 | **Expert 2 vs Expert 4** | 154 | **0.9917** | 0.9942 | 0.9896 | Near-Perfect Agreement |
| 6 | **Expert 3 vs Expert 4** | 154 | **0.8855** | 0.8974 | 0.8746 | Near-Perfect Agreement |
| — | **Arithmetic Mean** | — | **0.8167** | **0.8559** | **0.7753** | **Near-Perfect ($\kappa > 0.80$)** |

### 4.2 Multi-Rater Fleiss' Kappa Calculation
Fleiss' Kappa evaluates inter-rater reliability among $m = 4$ fixed raters assigning $N = 154$ subjects into $k = 3$ mutually exclusive categories:
- Observed subject agreement: $\bar{P} = 0.8853$
- Expected chance agreement: $\bar{P}_e = 0.4807$
- Multi-rater Fleiss' Kappa:
  $$\kappa_{\text{Fleiss}} = \frac{\bar{P} - \bar{P}_e}{1 - \bar{P}_e} = \frac{0.8853 - 0.4807}{1 - 0.4807} = \mathbf{0.7791}$$
Under Landis & Koch (1977) criteria, $\kappa \in [0.61, 0.80]$ denotes **Substantial Agreement**, confirming the high clarity and reproducibility of the AgileGraph cryptographic classification rubric.

---

## 5. Phase 3: Consensus Adjudication Audit

### 5.1 Adjudication Breakdown
- **Unanimous Agreement ($4/4$ or $3/3$)**: 117 assets (73.1%)
- **Majority Agreement ($3/4$ or $2/3$)**: 32 assets (20.0%)
- **Resolved Ties ($2\text{ vs }2$)**: 11 assets (6.9%) resolved deterministically using conservative precedence ($\text{HIGH} > \text{MEDIUM} > \text{LOW}$)
- **Total Adjudicated Assets**: Exactly 160

### 5.2 Audit of the 11 Resolved Tie Cases
In exactly 11 cases where the 4 raters split 2-to-2, conservative precedence was applied:

| Canonical Asset ID | Reviewer Votes | Consensus | Justification |
| :--- | :---: | :---: | :--- |
| `go_crypto:ssh/mlkem.go` | Exp1: MED, Exp2: LOW, Exp3: MED, Exp4: LOW | **MEDIUM** | Conservative tie-break: MED > LOW |
| `go_crypto:x509roots/nss/parser.go` | Exp1: LOW, Exp2: HIGH, Exp3: LOW, Exp4: HIGH | **HIGH** | Conservative tie-break: HIGH > LOW |
| `java_java_jwt:lib/src/main/java/com/auth0/jwt/interfaces/ECDSAKeyProvider.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_java_jwt:lib/src/main/java/com/auth0/jwt/interfaces/RSAKeyProvider.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_jjwt:api/src/main/java/io/jsonwebtoken/SignatureAlgorithm.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/DefaultRsaKeyAlgorithm.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/EcdhKeyAlgorithm.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/EdwardsPublicKeyDeriver.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/PrivateECKey.java` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |
| `python_cryptography:src/cryptography/x509/extensions.py` | Exp1: LOW, Exp2: HIGH, Exp3: LOW, Exp4: HIGH | **HIGH** | Conservative tie-break: HIGH > LOW |
| `python_cryptography:tests/hazmat/primitives/decrepit/test_rc2.py` | Exp1: HIGH, Exp2: MED, Exp3: HIGH, Exp4: MED | **HIGH** | Conservative tie-break: HIGH > MED |

### 5.3 Audit of the 6 Reviewer 4 Abstentions
Reviewer 4 marked 6 assets as unclassified with the rationale *"Insufficient context"*. These assets were adjudicated across the remaining 3 reviewers without tie-breaking:
1. `go_crypto:acme/autocert/listener.go`: 3 MEDIUM $\rightarrow$ **MEDIUM** (Unanimous, 1.0)
2. `go_crypto:pkcs12/pkcs12_test.go`: 1 HIGH, 2 MEDIUM $\rightarrow$ **MEDIUM** (Majority, 0.67)
3. `java_java_jwt:lib/src/test/java/com/auth0/jwt/PemUtils.java`: 1 HIGH, 2 MEDIUM $\rightarrow$ **MEDIUM** (Majority, 0.67)
4. `java_java_jwt:lib/src/test/java/com/auth0/jwt/algorithms/ECDSAAlgorithmTest.java`: 1 HIGH, 2 LOW $\rightarrow$ **LOW** (Majority, 0.67)
5. `java_java_jwt:lib/src/test/java/com/auth0/jwt/algorithms/ECDSABouncyCastleProviderTests.java`: 1 HIGH, 2 LOW $\rightarrow$ **LOW** (Majority, 0.67)
6. `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/Randoms.java`: 3 LOW $\rightarrow$ **LOW** (Unanimous, 1.0)

---

## 6. Phase 4: Model Evaluation & Misclassification Analysis

### 6.1 Performance Against Adjudicated Ground Truth
The heuristic engine outputs a normalized composite risk score $R(v) \in [0.0, 1.0]$, partitioned into:
- $\text{LOW}: R(v) < 0.35$
- $\text{MEDIUM}: 0.35 \le R(v) < 0.70$
- $\text{HIGH}: R(v) \ge 0.70$

| Metric | Point Estimate | 95% Bootstrap CI ($B = 1000$, Seed 42) |
| :--- | :---: | :---: |
| **Macro-Averaged F1** | **0.3225** | **[0.2558, 0.3799]** |
| **Linear Weighted Cohen's $\kappa$** | **0.2625** | — |
| **Accuracy** | **33.12%** (53/160) | — |

### 6.2 Confusion Matrix ($N = 160$ Assets)
$$\begin{pmatrix}
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{Expert LOW (29)} & \mathbf{26} & 1 & 2 \\
\text{Expert MED (51)} & 45 & \mathbf{2} & 4 \\
\text{Expert HIGH (80)} & 9 & 46 & \mathbf{25}
\end{pmatrix}$$

### 6.3 Detailed Per-Class Breakdown
- **LOW Class**:
  - Precision: $26 / (26 + 45 + 9) = 26 / 80 = \mathbf{0.3250}$
  - Recall: $26 / 29 = \mathbf{0.8966}$
  - F1-Score: $\mathbf{0.4771}$
  - Finding: AgileGraph correctly captures 89.7% of all human-adjudicated low-risk assets.
- **MEDIUM Class**:
  - Precision: $2 / (1 + 2 + 46) = 2 / 49 = \mathbf{0.0408}$
  - Recall: $2 / 51 = \mathbf{0.0392}$
  - F1-Score: $\mathbf{0.0400}$
  - Finding: Severe divergence due to heuristic risk dampening on unexposed symmetric ciphers.
- **HIGH Class**:
  - Precision: $25 / (2 + 4 + 25) = 25 / 31 = \mathbf{0.8065}$
  - Recall: $25 / 80 = \mathbf{0.3125}$
  - F1-Score: $\mathbf{0.4505}$
  - Finding: When AgileGraph labels an asset HIGH, it is validated by human experts with **80.65% precision**.

### 6.4 Scientific Explanation of the Heuristic vs. Expert Gap
The low overall Macro-F1 (0.3225) is an authentic, defensible scientific observation:
1. **The 46 "Expert HIGH, Heuristic MEDIUM" Assets**:
   Human experts evaluated public-key ciphers (`RSA`, `ECDSA`, `ECDH`) as intrinsically HIGH risk under Shor's algorithm regardless of context. However, 46 of these files reside in offline test suites (e.g. `acme/acme_test.go`, `autocert/autocert_test.go`) or internal helper packages. AgileGraph's 7-factor engine incorporates internet exposure ($w_{\text{exp}} = 0.15$), asset criticality ($w_{\text{crit}} = 0.15$), and library centrality ($w_{\text{cent}} = 0.15$). Because these test files have 0.0 exposure and non-production reachability, their composite risk was dampened into the $[0.35, 0.70)$ MEDIUM tier.
2. **The 45 "Expert MEDIUM, Heuristic LOW" Assets**:
   Human experts assigned MEDIUM risk to symmetric ciphers (`AES-128`, `ChaCha20`) or cryptographic wrappers based on Grover's key-halving search. AgileGraph's heuristic engine evaluated unexposed internal symmetric usages with adequate 128/256-bit keys as low migration urgency, assigning scores $< 0.35$.
3. **Implication**: Human experts assess *cryptographic primitive exploitability*, whereas AgileGraph models *contextual migration urgency*.

---

## 7. Phase 5 & 6: Architectural Integrity & System Invariants

### 7.1 Strict Data Isolation (Zero Training Leakage)
A static search across all Python code files confirmed that `expert_validation`, `expert_annotations`, and `AdjudicatedLabel` are referenced strictly in:
- `backend/scripts/run_expert_validation.py` (Analysis script)
- `backend/src/ml/expert_validation.py` (Data model)
- `backend/src/ml/agreement.py` (Statistical metrics)
- `backend/tests/ml/test_expert_validation.py` (Unit tests)
- `backend/tests/api/test_routes.py` (API status endpoint)
- `backend/tests/cli/test_cli.py` (CLI command)
No expert annotations or adjudicated labels are ever loaded into `backend/src/ml/gatv2.py`, `backend/src/ml/train.py`, or any training routine.

### 7.2 Mosca Readiness Formulation Verification
- Classical condition: $X + Y > Z$
- Normalized Urgency Index: $U = \frac{X + Y}{Z}$
- Consistency: $U > 1.0 \iff X + Y > Z$ yields `MoscaStatus.AT_RISK`
- Safety band: $0.8 \le U \le 1.0$ yields `MoscaStatus.URGENT`
- Safe band: $U < 0.8$ yields `MoscaStatus.SAFE`
- Verified: Frontend (`MoscaReadiness.tsx`) and Backend (`src/risk/mosca.py`) are strictly synchronized.

### 7.3 GNNExplainer Attribution
- Implementation: `backend/src/ml/explainability.py` (`HeteroExplainerModelWrapper` + PyG `Explainer`).
- API Endpoint: `GET /api/v1/projects/{project_id}/assets/{asset_id:path}/explanation` verified.
- Frontend Drawer: React 19 interactive drawer in `frontend/src/components/RiskAnalysis.tsx` verified.

### 7.4 Non-Claim Verification Regarding Unbundled External Tools
- External third-party tools are documented as exploratory prototypes that were formally unbundled and archived in `docs/archive/`.
- It is NOT claimed or evaluated as an integrated baseline in any academic report or benchmark table.

---

## 8. Phase 8: Comprehensive Test Execution Suite

### 8.1 Backend Pytest Execution
- Command: `pytest backend/tests/ -q`
- Result: **429 passed, 4 skipped in 27.33s** (0 failures).
- Skips: 4 symlink tests skipped due to Windows non-administrator filesystem constraints.
- ML Tests: `pytest backend/tests/ml/ -v` $\rightarrow$ **61 passed** in 10.36s.
- Forbidden Strings Invariant: `pytest backend/tests/core/test_forbidden_strings.py` $\rightarrow$ **Passed**.

### 8.2 Frontend Vitest & Build Execution
- Command: `npx vitest run`
- Result: **39 passed across 6 test files** in 4.45s (0 failures).
- Build Command: `npm run build`
- Result: **Clean production build exit 0** (`dist/index.html` generated in 1.49s).

---

## 9. Phase 9: Deliverables & Artifact Inventory

| Artifact Path | Format | Status | Description |
| :--- | :---: | :---: | :--- |
| `FINAL_VALIDATION_AUDIT.md` | Markdown | **Generated** | This comprehensive research audit report. |
| `backend/dataset/artifacts/expert_validation_report.json` | JSON | **Updated** | Machine-readable report with pairwise details, per-class metrics, and 160-item adjudication audit table. |
| `docs/AGILEGRAPH_PROJECT_SYNOPSIS.docx` | DOCX | **Regenerated** | Official Major Project Synopsis in IEEE / University format with updated 4-expert validation findings. |
| `docs/AGILEGRAPH_PROJECT_SYNOPSIS.pdf` | PDF | **Regenerated** | Standalone PDF synopsis with verified metrics and Mosca dual formulation. |
| `docs/evaluation.md` | Markdown | **Updated** | Section 8 added with comprehensive 4-expert validation audit and confusion matrix analysis. |

---

## 10. Reproducibility Guide

To reproduce every statistical metric and audit output from a clean shell:

```powershell
# 1. Activate Python virtual environment
cd "d:\projects\agilegraph new"
.\backend\venv\Scripts\Activate.ps1

# 2. Run the Expert Validation Pipeline
python backend/scripts/run_expert_validation.py

# 3. Verify Statistical Invariant Unit Tests
pytest backend/tests/ml/test_expert_validation.py -v

# 4. Run Full Backend Test Suite
pytest backend/tests/ -q

# 5. Run Frontend Test Suite and Production Build
cd frontend
npx vitest run
npm run build
cd ..

# 6. Regenerate Synopsis Documents
python scratch/generate_synopsis_docx.py
python scratch/generate_synopsis_pdf.py
```

---
*Signed and Certified by the AgileGraph Research & Development Team — November 2026.*

