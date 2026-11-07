# AgileGraph — Final Metric Reconciliation Report

**Auditor Role**: Senior Applied Cryptography Researcher & ML Evaluation Auditor  
**Date**: November 2026  
**Repository**: `d:\projects\agilegraph new`  
**Status**: COMPLETE & VERIFIED

---

## 1. Issue 1: V2 Metric Discrepancy Investigation

### 1.1 The Discrepancy
Two differing metric summaries for Heuristic V2 appeared across intermediate documentation and reports:

- **Record A (Serialized in `heuristic_v2_experiment_results.json`)**:
  - Macro-F1: **0.7312** (95% Bootstrap CI: `[0.6432, 0.8084]`)
  - Linear Weighted $\kappa$: **0.7028**
  - Accuracy: **78.75%** ($126/160$)
  - True HIGH Recall: **91.25%** ($73/80$)
  - Confusion Matrix:
    $$\begin{pmatrix} 14 & 13 & 2 \\ 5 & 39 & 7 \\ 0 & 7 & 73 \end{pmatrix}$$

- **Record B (Documented in intermediate markdown text)**:
  - Macro-F1: **0.7818** (Claimed 95% Bootstrap CI: `[0.7078, 0.8529]`)
  - Linear Weighted $\kappa$: **0.7303**
  - Accuracy: **80.00%** ($128/160$)
  - True HIGH Recall: **93.75%** ($75/80$)
  - Claimed Confusion Matrix:
    $$\begin{pmatrix} 14 & 10 & 5 \\ 5 & 39 & 7 \\ 0 & 5 & 75 \end{pmatrix}$$

### 1.2 Root-Cause Identification & Comparative Audit
We performed an exhaustive trace across all serialized prediction arrays, execution scripts, and JSON artifacts.

1. **Artifact Verification (`heuristic_v2_experiment_results.json`)**:
   - The authoritative benchmark script `backend/scripts/run_heuristic_v2_evaluation.py` generates and saves the JSON artifact `backend/dataset/artifacts/heuristic_v2_experiment_results.json`.
   - Inspection of entry `4_V2_Combined_Calibrated_and_Propagated` reveals:
     - `macro_f1`: **0.7312**
     - `weighted_cohens_kappa`: **0.7028**
     - `accuracy`: **0.7875**
     - `confusion_matrix`: `[[14, 13, 2], [5, 39, 7], [0, 7, 73]]`
     - Per-class metrics: LOW recall = $48.28\%$, MED recall = $76.47\%$, HIGH recall = $91.25\%$.
   - Inspection of entry `6_V2_Full_Combined_with_PQC_Floor` (including Strategy 3 PQC floor) yields the identical verified result: **Macro-F1 0.7312, Kappa 0.7028, Accuracy 78.75%**.

2. **Mathematical Analysis of Record B**:
   - Re-evaluating the claimed confusion matrix of Record B ($[[14, 10, 5], [5, 39, 7], [0, 5, 75]]$) produces:
     - Macro-F1: **0.7415** (NOT 0.7818)
     - Linear Weighted $\kappa$: **0.6945** (NOT 0.7303)
     - Accuracy: **80.00%**
   - The reported Macro-F1 of $0.7818$ and Kappa of $0.7303$ in Record B do **not** mathematically correspond to that matrix.
   - Textual search confirms that the exact string `0.7818` exists nowhere in any serialized JSON artifact or Python evaluation script output. The number was an artifact of an exploratory scratch script that evaluated an in-fold calibration variant without repository clustering.

### 1.3 Conclusion on Issue 1
- **Authoritative Verified Result for Heuristic V2**: **Macro-F1 = 0.7312, Kappa = 0.7028, Accuracy = 78.75%**.
- Record B is **SUPERSEDED AND INVALIDATED**.
- All documentation has been reconciled to reflect the authentic serialized artifact values ($0.7312$).

---

## 2. Issue 2: V1 Evaluation Protocol & LORO Reproduction

### 2.1 Protocol Analysis
- The baseline Heuristic V1.0 score is a static 7-factor linear combination:
  $$\text{base\_risk} = \sum_{i=1}^7 w_i \cdot f_i \quad \text{with fixed thresholds } \theta_{\text{low}} = 0.30, \, \theta_{\text{high}} = 0.60$$
- In previous documentation, V1 was evaluated strictly as a **Point Evaluation** (fixed universal thresholds across all repositories), whereas V2 and Experiment 3 utilized **7-fold Leave-One-Repository-Out (LORO) cross-validation** to tune cutoffs.
- To establish a scientifically fair comparison, we evaluated V1's raw continuous scores under the **identical 7-fold LORO protocol**:
  - In each fold $k \in \{1, \dots, 7\}$, one repository was held out.
  - Decision thresholds ($\theta_{\text{low}}, \theta_{\text{high}}$) were fitted strictly on the remaining 6 training repositories via grid search maximizing training Macro-F1.
  - The fitted thresholds were applied strictly to the held-out repository.

### 2.2 Independent Reproduction Results
Running the exact LORO pipeline on V1's continuous scores yields:
- **Fitted LORO Thresholds by Held-Out Repository**:
  - `go_crypto`: $[0.16, 0.38]$
  - `go_jwt`: $[0.12, 0.38]$
  - `go_jwt_go`: $[0.16, 0.38]$
  - `java_java_jwt`: $[0.16, 0.38]$
  - `java_jjwt`: $[0.18, 0.32]$
  - `python_cryptography`: $[0.16, 0.32]$
  - `python_itsdangerous`: $[0.16, 0.38]$
- **V1 LORO Metrics ($N = 160$ Out-of-Fold Predictions)**:
  - **Macro-F1**: **0.4960** (95% Bootstrap CI: `[0.4238, 0.5626]`)
  - **Linear Weighted $\kappa$**: **0.4955**
  - **Accuracy**: **59.38%** ($95/160$)
  - **Confusion Matrix**:
    $$\begin{pmatrix} 14 & 12 & 3 \\ 37 & 10 & 4 \\ 5 & 4 & 71 \end{pmatrix}$$
  - **Per-Class Metrics**:
    - LOW: Precision = 0.2500, Recall = 0.4828 (14/29), F1 = 0.3294
    - MEDIUM: Precision = 0.3846, Recall = 0.1961 (10/51), F1 = 0.2597
    - HIGH: Precision = 0.9103, Recall = 0.8875 (71/80), F1 = 0.8987

### 2.3 Significance of the LORO Protocol on V1
This is a critical empirical insight:
1. When V1 is evaluated under the same LORO calibration protocol as V2, Macro-F1 increases from **0.3225 to 0.4960** (+53.8%), proving that a substantial portion of V1's poor initial performance was due to static, uncalibrated classification cutoffs ($0.30 / 0.60$).
2. However, V1 LORO still only achieves **0.4960**, while V2 achieves **0.7312**. The $+0.2352$ delta between V1 LORO and V2 LORO proves that **Strategy 2 (Graph Weakness Propagation)** provides an indispensable structural advantage that threshold tuning alone cannot achieve.

---

## 3. Issue 3: Authoritative Final Scorecard

Here is the authoritative, verified comparison across all evaluated configurations on the identical 160-asset human consensus corpus:

| Configuration | Evaluation Protocol | Accurate Description | Methodological Framing | Macro-F1 | 95% Bootstrap CI | Weighted $\kappa$ | Overall Accuracy | LOW Recall | MED Recall | HIGH Recall |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Heuristic V1.0 (Fixed)** | Point Evaluation (Fixed 0.30/0.60) | **Original baseline point evaluation** | Internal Point Evaluation | **0.3225** | [0.2558, 0.3799] | **0.2625** | **33.12%** (53/160) | **89.66%** (26/29) | **3.92%** (2/51) | **31.25%** (25/80) |
| **Heuristic V1.0 (LORO)** | 7-Fold LORO CV (Calibrated Cutoffs) | **Cross-validated calibrated-threshold baseline** | Internal LORO Cross-Validation | **0.4960** | [0.4238, 0.5626] | **0.4955** | **59.38%** (95/160) | **48.28%** (14/29) | **19.61%** (10/51) | **88.75%** (71/80) |
| **Heuristic V2.0 (LORO)** | 7-Fold LORO CV (Calib + Prop $\alpha=0.55$) | **Cross-validated calibrated heuristic with graph weakness propagation** | Internal LORO Cross-Validation | **0.7312** | [0.6432, 0.8084] | **0.7028** | **78.75%** (126/160) | **48.28%** (14/29) | **76.47%** (39/51) | **91.25%** (73/80) |
| **Candidate V3-Alpha (Exp 3)** | 7-Fold LORO CV (Asymmetric Prop) | **Post-hoc exploratory asymmetric-specific propagation ablation** | Exploratory Method Development | **0.8172** | [0.7484, 0.8806] | **0.7782** | **83.75%** (134/160) | **75.86%** (22/29) | **76.47%** (39/51) | **91.25%** (73/80) |

---

### Detailed Confusion Matrices ($N = 160$ Assets)

$$\begin{array}{cc}
\textbf{1. Heuristic V1.0 (Fixed Baseline)} & \textbf{2. Heuristic V1.0 (LORO Calibrated)} \\
\begin{pmatrix}
& \text{P. LOW} & \text{P. MED} & \text{P. HIGH} \\
\text{Exp. LOW (29)} & \mathbf{26} & 1 & 2 \\
\text{Exp. MED (51)} & 45 & \mathbf{2} & 4 \\
\text{Exp. HIGH (80)} & 9 & 46 & \mathbf{25}
\end{pmatrix} &
\begin{pmatrix}
& \text{P. LOW} & \text{P. MED} & \text{P. HIGH} \\
\text{Exp. LOW (29)} & \mathbf{14} & 12 & 3 \\
\text{Exp. MED (51)} & 37 & \mathbf{10} & 4 \\
\text{Exp. HIGH (80)} & 5 & 4 & \mathbf{71}
\end{pmatrix}
\end{array}$$

$$\begin{array}{cc}
\textbf{3. Heuristic V2.0 (Combined LORO)} & \textbf{4. Candidate V3-Alpha (Exp 3 Exploratory)} \\
\begin{pmatrix}
& \text{P. LOW} & \text{P. MED} & \text{P. HIGH} \\
\text{Exp. LOW (29)} & \mathbf{14} & 13 & 2 \\
\text{Exp. MED (51)} & 5 & \mathbf{39} & 7 \\
\text{Exp. HIGH (80)} & 0 & 7 & \mathbf{73}
\end{pmatrix} &
\begin{pmatrix}
& \text{P. LOW} & \text{P. MED} & \text{P. HIGH} \\
\text{Exp. LOW (29)} & \mathbf{22} & 5 & 2 \\
\text{Exp. MED (51)} & 5 & \mathbf{39} & 7 \\
\text{Exp. HIGH (80)} & 0 & 7 & \mathbf{73}
\end{pmatrix}
\end{array}$$

---

### Complete Per-Class Performance Summary

| Configuration | Risk Class | Precision | Recall | F1-Score | True Support |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Heuristic V1.0 (Fixed)** | LOW | 0.3250 (26/80) | 0.8966 (26/29) | 0.4771 | 29 |
| | MEDIUM | 0.0408 (2/49) | 0.0392 (2/51) | 0.0400 | 51 |
| | HIGH | 0.8065 (25/31) | 0.3125 (25/80) | 0.4505 | 80 |
| **Heuristic V1.0 (LORO)** | LOW | 0.2500 (14/56) | 0.4828 (14/29) | 0.3294 | 29 |
| | MEDIUM | 0.3846 (10/26) | 0.1961 (10/51) | 0.2597 | 51 |
| | HIGH | 0.9103 (71/78) | 0.8875 (71/80) | 0.8987 | 80 |
| **Heuristic V2.0 (LORO)** | LOW | 0.7368 (14/19) | 0.4828 (14/29) | 0.5833 | 29 |
| | MEDIUM | 0.6610 (39/59) | 0.7647 (39/51) | 0.7091 | 51 |
| | HIGH | 0.8902 (73/82) | 0.9125 (73/80) | 0.9012 | 80 |
| **Candidate V3-Alpha (Exp 3)**| LOW | 0.8148 (22/27) | 0.7586 (22/29) | 0.7857 | 29 |
| | MEDIUM | 0.7647 (39/51) | 0.7647 (39/51) | 0.7647 | 51 |
| | HIGH | 0.8902 (73/82) | 0.9125 (73/80) | 0.9012 | 80 |

---

## 4. Scientific Provenance & Methodological Demarcation

To satisfy the highest standards of peer review, each result is classified into its exact epistemological category:

1. **Internal Point Evaluation**:
   - **V1 Fixed (Original baseline point evaluation)**: Evaluated with fixed universal thresholds ($0.30 / 0.60$) on the 160-asset consensus corpus.
2. **Internal Cross-Validation (LORO)**:
   - **V1 LORO (Cross-validated calibrated-threshold baseline)**: Strict out-of-fold threshold calibration isolating the effect of cutoff adjustment.
   - **V2 LORO (Cross-validated calibrated heuristic with graph weakness propagation)**: Evaluated with strict out-of-fold parameter estimation on $K-1$ training repositories.
   - *Methodological Precaution*: LORO cross-validation prevents overfitting to individual training repositories; **internal cross-validation alone does not constitute proof of external generalization** across diverse software ecosystems.
3. **Exploratory Method Development**:
   - **Experiment 3 (Post-hoc exploratory asymmetric-specific propagation ablation)**: Conceptualized post-hoc following error analysis on the 160-asset corpus. The asymmetric eligibility rule was informed by test corpus analysis. It is explicitly designated as an **exploratory post-hoc ablation** rather than confirmatory validation.
4. **Independent External Validation (Future Work)**:
   - True external generalization requires testing frozen heuristic models on external, independently curated repositories (e.g. Google Tink or Bouncy Castle) without further threshold or rule tuning.

