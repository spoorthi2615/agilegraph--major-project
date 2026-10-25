# AgileGraph — Final Verification, Reproducibility & Submission Readiness Audit Report

**Project Title:** AgileGraph — Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Degree / Context:** Final-Year B.Tech Cyber Security Major Project  
**Date of Audit:** October 25, 2026  
**Auditor:** Automated Independent Verification System  
**Repository Branch:** `chore/agilegraph-repository-cleanup`  
**Working Directory:** `d:\projects\agilegraph new`  

---

## 1. Executive Verdict

### **READY FOR SUBMISSION**

#### **Evidence and Justification:**
1. **Engineering Completeness & Test Passing:** 
   - All 390 executable backend tests pass without a single failure (`390 passed, 4 skipped in 32.75s`). The 4 skipped tests are strictly due to Windows OS filesystem constraints (Unix FIFOs and non-elevated symlinks).
   - All 27 frontend unit and integration tests pass cleanly (`27 passed in 2.55s`).
   - The React / Vite frontend production build compiles with zero errors (`built in 850ms`).
2. **End-to-End Operability:**
   - Both the CLI (`python backend/src/cli.py scan ...`) and the FastAPI backend (`uvicorn src.main:app`) operate end-to-end, producing property graphs, deterministic 7-factor heuristic risk scores, cryptographic inventories, and Markdown/JSON security audit reports.
3. **Scientific Soundness & Metric Reconciliation:**
   - The heterogeneous GATv2 model was audited and verified through 8-fold Leave-One-Project-Out (LOPO) cross-validation across all 8 benchmark repositories ($N = 520$ file assets).
   - Recalculated aggregate metrics strictly confirm: **Accuracy = 66.73%**, **Balanced Accuracy = 54.18%**, **Macro-F1 = 0.5560**, **Macro-Precision = 69.75%**, **Macro-Recall = 54.18%**.
   - The Static Rule baseline bug (previously reading index 0 instead of index 3 for `crypto_weakness`) was corrected, and the verified baseline values are **42.12% accuracy and 0.4119 macro-F1** (outperforming the 22.69% majority baseline).
   - The Target Leakage experiment was clarified: the earlier 98.31% result was an artifact of training-set memorization on `python_cryptography`, whereas the genuine cross-repository LOPO leakage ablation demonstrates that injecting target-derived `base_risk` artificially inflates generalization from **66.73% to 83.08%** ($+16.35\%$).
4. **Architectural Safeguards Confirmed in Code:**
   - Because the high-risk class recall is **27.2%** (due to 99 of 103 high-risk files concentrating in `python_cryptography`), the codebase treats the GNN strictly as an **enrichment and prioritization layer**. Deterministic AST code scanners and heuristic rules independently compute and report all detected cryptographic weaknesses. Known quantum-vulnerable primitives (RSA, DSA, weak ECC) are **never** suppressed or bypassed by the GNN.
5. **No Fabricated Data:**
   - All obsolete synthetic expert-panel annotation artifacts, fabricated Cohen's Kappa claims, and placeholder scripts from legacy phases were removed.

---

## 2. Verification Summary

| Verification Area | Status | Exact Evidence | Remaining Issue / Limitation | Recommended Action |
|---|---|---|---|---|
| **Repository Completeness** | **PASS** | Clean directory structure; backend, frontend, CLI, scripts, and docs present. | Local corpus git trees removed to save space; `.pt` graphs pinned. | Keep `.pt` graph artifacts tracked in Git. |
| **GATv2 Architecture** | **PASS** | `HeteroGATv2` with `GATv2Conv`, `HeteroConv`, input projections, and residual connections. | Heterogeneous edge metadata requires PyG lazy initialization. | Pre-initialize lazy modules before checkpoint cloning. |
| **Model Training Loop** | **PASS** | Gradient backprop verified: initial loss $1.3017 \to 0.6469$, parameter L2 delta $0.3765 > 1e-6$. | None. Training loop updates weights deterministically. | None. |
| **LOPO Evaluation ($N=520$)** | **PASS** | 8 folds executed out-of-fold. Recalculated: Acc 66.73%, Bal-Acc 54.18%, Macro-F1 0.5560. | High-risk recall is 27.2% (28/103) due to domain imbalance. | Frame GNN as risk enrichment, not standalone blocker. |
| **Baseline Comparisons** | **PASS** | Majority: 22.69% acc, 0.1321 F1. Corrected Static Rule: 42.12% acc, 0.4119 F1. | Static rule previously used index 0; index 3 fix confirmed. | Cite 42.12% / 0.4119 in viva and report. |
| **Target Leakage Ablation** | **PASS** | Cross-repo LOPO: 66.73% (genuine 14-dim) vs 83.08% (leaked 15-dim). | Previous 98.31% was training-set memorization ($N=178$). | Document as an intentional leakage demonstration. |
| **7-Factor Risk Engine** | **PASS** | Canonical weights sum to 1.0 (crypto_weakness = 0.25). Missingness masks handled. | Centrality requires connected library nodes for non-zero blast radius. | Verified in `calculate_library_centrality_for_file`. |
| **Backend Test Suite** | **PASS** | `python -m pytest backend/tests`: 390 passed, 4 skipped in 32.75s. | 4 skipped tests are Windows OS symlink/FIFO restrictions. | None. Fully verified. |
| **Frontend Test Suite** | **PASS** | `npm test` (`vitest run`): 27 passed in 2.55s across 4 test suites. | JSDOM environment has harmless jsdom navigation warning. | None. Fully verified. |
| **Frontend Build** | **PASS** | `npm run build`: `tsc -b && vite build` completed in 850ms with 0 errors. | Single minified JS bundle warning (>500kB). | Standard Vite output; zero compile errors. |
| **FastAPI Backend Operability** | **PASS** | Tested `/api/v1/scan`, `/projects/.../graph`, `/projects/.../risk`, `/product/...`. All return 200 OK. | None. | Document exact endpoint URLs. |
| **CLI Functionality** | **PASS** | `cli.py scan` and `cli.py report` executed on `python_itsdangerous` (19 nodes, 7 assets). | None. | Use `python backend/src/cli.py` syntax. |
| **Clean-Checkout Reproducibility** | **PASS** | `backend/requirements.txt`, `package.json`, and pinned `.pt` graphs allow offline execution. | Re-cloning raw corpus from GitHub requires internet access. | Note that pinned `.pt` artifacts allow 100% offline run. |
| **Documentation Consistency** | **PASS** | `README.md`, `docs/evaluation.md`, and JSON results synchronized. | None. | Freeze documentation. |

---

## 3. Repository Completeness

### Directory and Component Audit

| Component | Expected Files / Paths | Actual Status | Verification Evidence |
|---|---|---|---|
| **Backend Core** | `backend/src/main.py`, `backend/src/cli.py` | Complete & Functional | FastAPI entrypoint and argparse CLI operational. |
| **Scanners** | `backend/src/scanners/{python,java,go,certificates,endpoints,sensitive_data,dependencies}` | Complete & Functional | Tested across all languages; unit tests in `backend/tests/scanners/` pass. |
| **Graph Modeling** | `backend/src/graph/{graph,builder,schema,validation}.py` | Complete & Functional | Enforces 6 node types and 11 edge relationships; NetworkX property graph verified. |
| **Risk Engine** | `backend/src/risk/{factors,heuristic,weights,centrality,criticality,sensitivity,exposure,cve_risk,mosca}.py` | Complete & Functional | Canonical weights sum to 1.0; missing-data renormalization operational. |
| **ML Engine** | `backend/src/ml/{gatv2,converter,features,pipeline,evaluation,experiment}.py` | Complete & Functional | `HeteroGATv2`, 14-dim feature vector, and LOPO training pipeline operational. |
| **Dataset Artifacts** | `backend/dataset/artifacts/{8 .pt files, manifest.json, report.json, gatv2_evaluation_results.json}` | Complete & Validated | All 8 `.pt` graphs load without error; 520 files accounted for. |
| **Evaluation Scripts** | `backend/scripts/{build_corpus.py, corpus_summary.py, run_gatv2_evaluation.py, generate_case_studies.py}` | Complete & Functional | Executed and confirmed to generate reports and verify claims. |
| **Frontend UI** | `frontend/src/{App.tsx, components/, api/client.ts}` | Complete & Functional | React dashboard, Graph view, Inventory table, Reports view, and PQC Readiness operational. |
| **Configuration** | `backend/pytest.ini`, `backend/src/config/heuristic_weights.json`, `frontend/vite.config.ts` | Complete & Functional | Configurable weights, test paths, and API proxy configured. |
| **Documentation** | `README.md`, `docs/{evaluation, quality_control, reproducibility}.md` | Complete & Synchronized | Free of fabricated metrics; limitations and baseline corrections documented. |

---

## 4. ML Training and Artifacts

### 4.1 Actual Model Architecture
- **Class**: `HeteroGATv2` defined in `backend/src/ml/gatv2.py`.
- **Base Components**: PyTorch Geometric `torch_geometric.nn.GATv2Conv`, wrapped in `HeteroConv` with `aggr='sum'`, and per-node-type `Linear(-1, hidden_channels)` projections.
- **Hidden Channels**: 32.
- **Attention Heads**: 2 (per layer).
- **Layers**: 2 Heterogeneous Convolution layers with residual fallback connections (`h_dict[key] + F.elu(out[key])`).
- **Output Layer**: Linear classification head mapping hidden channels to 3 risk classes (LOW=0, MEDIUM=1, HIGH=2).

### 4.2 Feature Construction (14 Dimensions)
The feature vector for `file` nodes is strictly constructed in `backend/src/ml/features.py` (`extract_node_features`):
- **7 Factor Values**: `data_sensitivity`, `asset_criticality`, `internet_exposure`, `crypto_weakness`, `cve_risk`, `library_centrality`, `migration_difficulty`.
- **7 Observation Masks**: $0.0$ if the factor is observed in code or metadata; $1.0$ if the factor is missing/unobserved.
- **Target Leakage Safeguard**: Continuous `base_risk` is **strictly excluded** (`include_base_risk=False` by default).

### 4.3 Training Configuration and Verification
- **Loss Function**: `nn.CrossEntropyLoss(weight=weights_tensor)` with inverse class frequency weights to counteract class imbalance.
- **Optimizer**: `optim.Adam(model.parameters(), lr=0.005)`.
- **Epochs**: 15 epochs per fold in LOPO evaluation; 20 epochs in repository-split evaluation.
- **Parameter Update Verification**:
  - Initial Loss: **1.3017**
  - Final Loss: **0.6469** (Loss reduction: **0.6548**)
  - Parameter L2 Norm Delta: **0.3765** (verifying that backpropagation actively updates weights).

### 4.4 Checkpoint and Artifact Locations
- **Corpus Graph Artifacts**: `backend/dataset/artifacts/{go_crypto, go_jwt, go_jwt_go, java_java_jwt, java_jjwt, python_bcrypt, python_cryptography, python_itsdangerous}.pt`
- **Evaluation Results**: `backend/dataset/artifacts/gatv2_evaluation_results.json`
- **Synthetic Development Sandbox Checkpoints**: `backend/dataset/synthetic_dev_sandbox/{dev_checkpoint_without_base_risk.pt, dev_checkpoint_with_base_risk.pt, dev_checkpoint_structure_only.pt}`

---

## 5. Evaluation Results and Scientific Limitations

### 5.1 Dataset Demographics and Class Distribution

| Repository | Language | File Assets | LOW (Class 0) | MEDIUM (Class 1) | HIGH (Class 2) | Unrated |
|---|---|---:|---:|---:|---:|---:|
| `go_crypto` | GO | 111 | 75 | 34 | 2 | 0 |
| `go_jwt` | GO | 20 | 12 | 8 | 0 | 0 |
| `go_jwt_go` | GO | 19 | 6 | 12 | 1 | 0 |
| `java_java_jwt` | JAVA | 18 | 15 | 3 | 0 | 0 |
| `java_jjwt` | JAVA | 170 | 164 | 6 | 0 | 0 |
| `python_bcrypt` | PYTHON | 1 | 0 | 1 | 0 | 0 |
| `python_cryptography` | PYTHON | 178 | 2 | 77 | **99** | 0 |
| `python_itsdangerous` | PYTHON | 3 | 2 | 0 | 1 | 0 |
| **Total Corpus** | **3 Languages** | **520** | **276 (53.1%)** | **141 (27.1%)** | **103 (19.8%)** | **0** |

### 5.2 Recalculated Out-of-Fold LOPO Metrics ($N = 520$)

| Evaluation Model / Baseline | Accuracy | Balanced Accuracy | Macro-F1 | Macro-Precision | Macro-Recall |
|---|---:|---:|---:|---:|---:|
| **GATv2 (LOPO Out-of-Fold)** | **66.73%** | **54.18%** | **0.5560** | **69.75%** | **54.18%** |
| **Majority Class Baseline** | 22.69% | 14.95% | 0.1321 | 11.84% | 14.95% |
| **Corrected Static Rule Baseline** | **42.12%** | **43.14%** | **0.4119** | **53.96%** | **43.14%** |
| **Heuristic Teacher Baseline** | *100.0%* | *100.0%* | *1.0000* | *100.0%* | *100.0%* |

### 5.3 Aggregate Confusion Matrix ($N = 520$ Out-of-Fold Files)

$$\begin{pmatrix} 
& \text{Predicted LOW} & \text{Predicted MEDIUM} & \text{Predicted HIGH} \\
\text{True LOW (0)} & \mathbf{262} & 12 & 2 \\
\text{True MEDIUM (1)} & 83 & \mathbf{57} & 1 \\
\text{True HIGH (2)} & 26 & 49 & \mathbf{28}
\end{pmatrix}$$

- **Class 0 (LOW, $N=276$)**: Precision = **70.62%**, Recall = **94.93%**, F1 = **0.8099**
- **Class 1 (MEDIUM, $N=141$)**: Precision = **48.31%**, Recall = **40.43%**, F1 = **0.4402**
- **Class 2 (HIGH, $N=103$)**: Precision = **90.32%**, Recall = **27.18% (28 / 103)**, F1 = **0.4179**

### 5.4 Controlled Target Leakage Ablation

| Regime | Features | Evaluation Protocol | Accuracy | Macro-F1 | Finding |
|---|---|---|---:|---:|---|
| **WITHOUT_BASE_RISK** | 14-dim genuine | Cross-Repo LOPO ($N=520$) | **66.73%** | **0.5560** | Genuine graph structural generalization. |
| **WITH_BASE_RISK** | 15-dim target leaked | Cross-Repo LOPO ($N=520$) | **83.08%** | **0.7185** | **+16.35% artificial boost** from leaking target shortcut. |
| *Resubstitution* | 14-dim or 15-dim | Training Set (`python_cryptography`, $N=178$) | 98.31% | 0.6595 | 15k parameters memorize 178 training nodes. |

### 5.5 Critical Scientific Limitations for Viva Defense
1. **Weak Supervision Nature**: Labels were generated by thresholding AgileGraph's heuristic formula ($<0.30, [0.30, 0.60), \ge 0.60$). The model evaluates **representation learning and structural knowledge distillation**, not independent empirical discovery of quantum vulnerability.
2. **High-Risk Class Concentration**: 99 of the 103 high-risk files in the entire benchmark belong to `python_cryptography`. In Fold 7 (holding out `python_cryptography`), training contains only 4 high-risk files ($1.1\%$), yielding low fold accuracy ($15.7\%$). When `python_cryptography` is in the training set (Folds 1–6, 8), held-out accuracy is 75.0%–97.6%.
3. **High-Risk Recall of 27.2%**: The GNN identifies 28 of 103 high-risk files. This justifies why the GNN is strictly an **enrichment layer**, while deterministic static scanners serve as the authoritative gatekeeper.

---

## 6. Backend and Frontend Tests

### 6.1 Backend Test Results (`pytest`)
- **Command:** `python -m pytest backend/tests`
- **Exit Code:** `0`
- **Summary:** **390 passed, 4 skipped in 32.75s**
- **Skipped Tests Detail:**
  1. `backend/tests/pipeline/test_runner_filesystem.py:65`: Symlink creation on Windows without developer mode.
  2. `backend/tests/pipeline/test_runner_filesystem.py:89`: Symlink traversal on Windows.
  3. `backend/tests/pipeline/test_runner_filesystem.py:105`: Unix FIFO pipe not supported on Windows.
  4. `backend/tests/pipeline/test_runner_filesystem.py:169`: Symlink escape test on Windows.

### 6.2 Frontend Test Results (`vitest`)
- **Command:** `npm test` (`vitest run`) in `frontend/`
- **Exit Code:** `0`
- **Summary:** **27 passed in 2.55s across 4 test suites**
  - `src/tests/Reports.test.tsx`: 8 passed
  - `src/tests/ProductLayer.test.tsx`: 10 passed
  - `src/tests/CryptoInventory.test.tsx`: 8 passed
  - `src/tests/AppIntegration.test.tsx`: 1 passed

### 6.3 Frontend Production Build (`vite build`)
- **Command:** `npm run build` (`tsc -b && vite build`) in `frontend/`
- **Exit Code:** `0`
- **Summary:** Built successfully in **850ms** with zero errors (`dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css`).

---

## 7. End-to-End Demonstration

The full scan and reporting lifecycle was verified across both CLI and API interfaces:

### 7.1 CLI Smoke Test
- **Command:** `python backend/src/cli.py scan "backend/dataset/corpus/python_itsdangerous" --output "backend/dataset/cache/cli_demo_result.json" --project-id "python_itsdangerous_demo"`
- **Observed Output:**
  ```text
  Scan complete. Found 19 nodes and 7 vulnerable assets.
  Report written to backend/dataset/cache/cli_demo_result.json
  ```
- **Markdown Generation:** `python backend/src/cli.py report "backend/dataset/cache/cli_demo_result.json" --output "backend/dataset/cache/cli_demo_report.md"`
- **Result:** Successfully generated a 12KB structured security audit report with complete factor breakdowns, provenance metadata, and operational estimate disclaimers.

### 7.2 FastAPI API Smoke Test
- In-process HTTP testing verified:
  - `POST /api/v1/scan` $\to$ `200 OK` (scanned 19 nodes, scored 7 assets)
  - `GET /api/v1/projects/{id}/graph` $\to$ `200 OK` (returns 19 NetworkX nodes)
  - `GET /api/v1/projects/{id}/risk` $\to$ `200 OK` (returns 7 evaluated risk scores)
  - `GET /api/v1/product/{id}/crypto-inventory` $\to$ `200 OK` (returns 19 total assets, 1 crypto usage)
  - `GET /api/v1/product/{id}/pqc-readiness` $\to$ `200 OK`
  - `POST /api/v1/product/mosca` $\to$ `200 OK` (evaluates $X=5, Y=10, Z=20 \to U=0.75$, status: SAFE)
  - `GET /api/v1/projects/{id}/report/markdown` $\to$ `200 OK`

---

## 8. Clean-Checkout Reproducibility

### 8.1 Setup in a Fresh Environment
1. **Python Environment**:
   - Requires Python 3.10+ (tested on Python 3.13).
   - `pip install -r backend/requirements.txt` installs all dependencies: `fastapi`, `uvicorn`, `pydantic`, `pytest`, `networkx`, `cryptography`, `torch`, `torch_geometric`, `scikit-learn`.
2. **Node.js Environment**:
   - Requires Node.js 18+ and npm.
   - `cd frontend && npm install` cleanly installs dependencies from `package-lock.json`.
3. **Corpus Availability**:
   - The 8 canonical PyG graphs are pre-processed and pinned in `backend/dataset/artifacts/*.pt`. This enables 100% offline testing, evaluation, and inference without needing to re-clone gigabytes of raw git repositories.
   - If raw rebuilding is desired, `backend/scripts/build_corpus.py` clones each repository at its exact pinned commit SHA recorded in `manifest.json`.

---

## 9. Documentation and Metric Consistency Audit

Every project document was audited against the verified metrics:

| Document | Verified Figures | Integrity Status |
|---|---|---|
| `README.md` | Section 13 reflects 66.73% LOPO accuracy, 0.5560 macro-F1, 22.69% majority baseline, 42.12% corrected static-rule baseline, and weak-supervision caveats. | **Consistent** |
| `docs/evaluation.md` | Contains full LOPO table, confusion matrix, 42.12% corrected baseline, 83.08% vs 66.73% leakage ablation, and 27.2% high-risk recall analysis. | **Consistent** |
| `docs/reproducibility.md` | Describes CLI scan commands and deterministic output constraints. | **Consistent** |
| `backend/dataset/artifacts/gatv2_evaluation_results.json` | Authoritative JSON output matching all recalculated figures to 4 decimal places. | **Consistent** |

All old references to 40.38% static-rule accuracy and 0.3022 macro-F1 have been eliminated.

---

## 10. Changes Made

During the Stage 1–3 audits and this final verification, the following minimal, targeted fixes were made:
1. `backend/scripts/run_gatv2_evaluation.py`: Fixed static-rule baseline feature index from 0 (`data_sensitivity`) to 3 (`crypto_weakness`), correcting accuracy from 40.38% to 42.12% and macro-F1 from 0.3022 to 0.4119.
2. `backend/scripts/run_gatv2_evaluation.py`: Updated leakage ablation to execute out-of-fold LOPO cross-validation, demonstrating an 83.08% vs 66.73% (+16.35%) impact, while clarifying that earlier 98.31% was intra-repo train set memorization.
3. `backend/tests/dataset/test_file_accounting.py` & `test_benchmark_step3.py`: Replaced hardcoded relative paths with `__file__`-relative path resolution so pytest runs cleanly from both root and backend directories.
4. `backend/pytest.ini`: Added `--ignore=backend/dataset` to prevent pytest from discovering vendor unit tests in raw corpus subdirectories.
5. `backend/src/cli.py`: Added `sys.path` bootstrap for direct command execution.
6. `docs/evaluation.md`: Authored full empirical evaluation documentation with verified confusion matrices and scientific caveats.
7. `backend/dataset/artifacts/gatv2_evaluation_results.json`: Regenerated with corrected static rule baseline and cross-repo leakage findings.

*Zero unnecessary refactoring, stylistic rewriting, git commits, or git pushes were performed.*

---

## 11. Known Limitations (Summary for Viva Defense)

1. **Heuristic Weak Supervision**: The labels are generated by a multi-factor risk formula. The model evaluates representation distillation rather than predicting actual historical security incidents.
2. **Domain Concentration**: 99 of the 103 high-risk file assets reside in `python_cryptography`. This heavy imbalance makes cross-repository high-risk transfer challenging (27.2% recall).
3. **Small Repositories**: Repositories like `python_bcrypt` ($N=1$) and `python_itsdangerous` ($N=3$) provide very small held-out test sets in their respective folds.
4. **Architectural Role**: Because GNN high-risk recall is 27.2%, the GNN is strictly used to enrich and rank risk, while deterministic AST scanners independently detect and report all known cryptographic weaknesses.

---

## 12. Final Submission Checklist

- [x] **Backend test suite passing**: 390 passed, 4 skipped (Windows-specific).
- [x] **Frontend test suite passing**: 27 passed, 0 failed.
- [x] **Frontend production build**: 0 errors.
- [x] **GATv2 training loop**: Gradient backpropagation and parameter updates verified.
- [x] **LOPO cross-validation**: 8 folds verified (Acc: 66.73%, F1: 0.5560).
- [x] **Baselines verified**: Majority (22.69%), Corrected Static Rule (42.12%).
- [x] **Target leakage ablation verified**: 83.08% vs 66.73% (+16.35% boost).
- [x] **Corpus accounting verified**: 8 repositories, 520 file assets accounted for.
- [x] **API and CLI operability verified**: Both scan and report generation succeed.
- [x] **Architectural safeguards verified in code**: Zero suppression of scanner findings.
- [x] **Obsolete files removed**: Expert annotation packages and legacy scripts cleaned.
- [x] **Documentation consistency**: All tables and README sections synchronized.

---

## 13. Exact Commands for the Student

Below is the verified, minimal set of real commands to run and demonstrate the project:

### 1. Run Backend Tests
```bash
python -m pytest backend/tests
```

### 2. Run Frontend Tests
```bash
cd frontend
npm test
cd ..
```

### 3. Build Frontend Production Bundle
```bash
cd frontend
npm run build
cd ..
```

### 4. Run CLI Scanning Demo
```bash
python backend/src/cli.py scan "backend/dataset/corpus/python_itsdangerous" --output "backend/dataset/cache/demo_scan.json" --project-id "demo_proj"
```

### 5. Generate Markdown Security Audit Report
```bash
python backend/src/cli.py report "backend/dataset/cache/demo_scan.json" --output "backend/dataset/cache/demo_report.md"
```

### 6. Start the Backend API Server
```bash
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 7. Start the Frontend Development Dashboard
```bash
cd frontend
npm run dev
```
*Open `http://localhost:5173` in your browser.*

### 8. Reproduce GATv2 LOPO Evaluation & Baselines
```bash
python backend/scripts/run_gatv2_evaluation.py
```
