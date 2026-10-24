# AgileGraph — Pre-Training Research Readiness & Evaluation Protocol

**Project Title:** Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Document Status:** Ready for Academic Project Guide Review  
**Date:** October 12, 2026  
**Version:** 3.0.0-RESEARCH-READY  
**Principle:** Complete methodological transparency. Zero training on synthetic data. Strict blinding & provenance isolation.

---

## 1. Research Problem and Experimental Objectives

AgileGraph investigates whether graph neural networks (specifically Heterogeneous GATv2) can learn migration prioritization for post-quantum cryptographic transitions directly from software call graphs, dependency structures, and cryptographic usage contexts—outperforming or refining static rule-based analysis and heuristic baseline scoring.

### Research Hypotheses
- **$H_1$ (Relational Agility Superiority):** GATv2 trained on heterogeneous code property graphs achieves higher macro-averaged $F_1$ than static rule-based baselines and linear heuristic combinations when evaluated on held-out repositories.
- **$H_2$ (Structural Synergy):** Relational information passing over dependency and AST edges enables accurate prioritization even when composite scalar risk priors are withheld (`WITHOUT_BASE_RISK` ablation).

---

## 2. Benchmark Corpus & Repository-Disjoint Splitting

The empirical benchmark comprises $N = 1,432$ files across 8 pinned open-source repositories spanning three major programming languages:

| Repository Identifier | Language | Ecosystem | Pinned Commit SHA | Total Files | Sampled Review Dossiers |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `python_cryptography` | Python | Cryptographic Primitives | `b99e745` | 1,013 | 50 |
| `python_itsdangerous` | Python | Web Security / Signing | `1298d02` | 7 | 7 |
| `python_bcrypt` | Python | Password Hashing | `5c3e6ef` | 2 | 2 |
| `go_crypto` | Go | Cryptographic Subpackages | `fc9a228` | 108 | 25 |
| `go_jwt` | Go | Token Verification | `b38e0c8` | 30 | 15 |
| `go_jwt_go` | Go | Token Verification | `0ad03d0` | 26 | 12 |
| `java_jjwt` | Java | JWT Security Framework | `d12760c` | 212 | 35 |
| `java_java_jwt` | Java | JWT Verification | `2cb071e` | 34 | 20 |
| **Total** | **3 Languages** | **8 Repositories** | **Exact Commits Pinned** | **1,432** | **166** |

### Repositories Assigned to Partitions (Language-Balanced Inductive Split — Protocol A)

To eliminate transductive feature leakage across repositories while ensuring cross-language generalization:

- **Training Partition (4 Repositories — 92 Assets)**:
  - `python_cryptography` (50 assets) [Python]
  - `python_itsdangerous` (7 assets) [Python]
  - `go_jwt` (15 assets) [Go]
  - `java_java_jwt` (20 assets) [Java]
  - *Language representation: Python: 57, Go: 15, Java: 20*
- **Validation Partition (2 Repositories — 14 Assets)**:
  - `python_bcrypt` (2 assets) [Python]
  - `go_jwt_go` (12 assets) [Go]
  - *Language representation: Python: 2, Go: 12*
- **Held-Out Test Partition (2 Repositories — 60 Assets)**:
  - `go_crypto` (25 assets) [Go]
  - `java_jjwt` (35 assets) [Java]
  - *Language representation: Go: 25, Java: 35*

> [!IMPORTANT]
> **Zero assets or graph nodes from `go_crypto` and `java_jjwt` will ever be seen during model training, tuning, or early stopping.**

---

## 3. Ground-Truth Elicitation & Expert Annotation Protocol

### 3.1 Reviewer Recruitment and Workload
- **Target Reviewers:** 4 independent cryptography and application security practitioners.
- **Blinding Integrity:** Evaluators are blinded to all heuristic scores (`base_risk`), baseline rankings, Mosca flags, and GNN predictions.
- **Dossiers:** Exactly 166 observable code evidence profiles across the 8 benchmark repositories.
- **Annotation Rubric (7 Dimensions):**
  1. *Primary Migration Priority (Ordinal Target)*: `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN` (Abstention).
  2. *Cryptographic Concern*: Classical Broken, Classical Vulnerable PQC, Quantum Vulnerable Strong, Post-Quantum Ready.
  3. *Sensitive Data Impact*: Credentials/Secrets, Personal Data/PII, Communication Content, Integrity Token, Ancillary.
  4. *Exposure Level*: Internet-Facing, Internal, Not Applicable, Unknown.
  5. *Post-Quantum Urgency*: Immediate Action, Planned Migration, Monitor, Investigate Further.
  6. *Evidence Confidence*: High, Medium, Low.
  7. *Rationale*: Free-text justification.

### 3.2 Inter-Rater Reliability Threshold
- **Primary Metric:** Ordinal Krippendorff’s Alpha ($\alpha$) per Krippendorff (2011):
  $$\alpha = 1 - \frac{D_o}{D_e}$$
- **Preregistered Gate:** $\alpha \ge 0.80$ is required for research consensus validation. ($0.67 \le \alpha < 0.80$ permits tentative exploratory analysis only).
- **Consensus Adjudication:** For items where raters disagree, majority vote or lead panel adjudication resolves ties. Unresolvable items are marked `UNKNOWN` and masked ($y = -1$).

---

## 4. AHP-Lite Heuristic Weight Derivation

Before finalizing the linear baseline:
$$\text{base\_risk} = \sum_{j=1}^7 w_j f_j, \quad \sum w_j = 1.0$$
The 7 factor weights ($w_1 \dots w_7$) are elicitable via an **AHP-Lite Survey** ([`backend/src/risk/ahp.py`](file:///d:/projects/agilegraph%20new/backend/src/risk/ahp.py)):
- Exactly 21 pairwise comparisons on Saaty's 1–9 fundamental scale.
- Evaluated via principal right eigenvector method: $A w = \lambda_{\max} w$.
- Consistency Ratio checked against random index $RI = 1.32$ ($n=7$):
  $$CI = \frac{\lambda_{\max} - 7}{6}, \quad CR = \frac{CI}{1.32} < 0.10$$
- Group aggregation across experts via geometric mean matrix aggregation (AHP-WGMM).

---

## 5. Weight Sensitivity Analysis Protocol

Automated one-at-a-time (OAT) sensitivity sweeps ([`backend/src/risk/sensitivity_analysis.py`](file:///d:/projects/agilegraph%20new/backend/src/risk/sensitivity_analysis.py)):
- Perturbations: Each factor perturbed independently by $-20\%$, $-10\%$, $+10\%$, $+20\%$ (28 runs).
- Simplex Renormalization: Non-perturbed weights adjusted proportionally to strictly preserve $\sum w_j = 1.0$.
- Stability Indicators:
  - Mean and maximum absolute score changes.
  - Spearman’s rank correlation ($\rho$) and Kendall’s rank correlation ($\tau$).
  - Top-10 and Top-20 migration set overlap ratios.

---

## 6. Baselines & Comparative Systems

To ensure a fair comparison, all systems are evaluated on the **exact same 60 held-out test assets**:

1. **Heuristic Baseline (`HeuristicBaseline`):**
   Continuous score $s \in [0.0, 1.0]$ mapped to ordinal priority via fixed operational thresholds:
   $$\hat{y} = \begin{cases} \text{HIGH} & \text{if } s \ge 0.80 \\ \text{MEDIUM} & \text{if } 0.50 \le s < 0.80 \\ \text{LOW} & \text{if } s < 0.50 \end{cases}$$
2. **Rule-Based Baseline (`RuleBasedBaseline`):**
   Deterministic static rule matching on algorithm identifiers and imports (e.g. classical broken/asymmetric algorithms $\rightarrow$ HIGH, symmetric $\rightarrow$ MEDIUM, PQC $\rightarrow$ LOW).

---

## 7. Model Architecture & Leakage Ablations

### GATv2 Architecture
- **Backbone:** 2-layer `HeteroConv` with `GATv2Conv` heads ($H=4$), ELU activations, and node-type-specific linear projections across all 6 node categories (`file`, `crypto_usage`, `library`, `certificate`, `endpoint`, `sensitive_data`).
- **Optimization:** AdamW ($\text{lr} = 10^{-3}$, weight decay $= 10^{-4}$), Cross-Entropy Loss with class weighting for imbalance.

### Experimental Regimes (Leakage Ablations)
1. **Primary Evaluation (`WITHOUT_BASE_RISK`):**
   Input features comprise the 7 raw context factors and 7 binary missingness flags (14 dimensions total). The composite scalar `base_risk` is strictly withheld. Tests non-linear graph synthesis.
2. **Structure-Only Benchmark (`STRUCTURE_ONLY`):**
   Node feature vector is pinned to $x_i = [0.0]$. The GNN makes predictions solely based on node categories, degree distribution, and graph neighborhood topology.
3. **Diagnostic Prior Run (`WITH_BASE_RISK`):**
   Input features include `base_risk` (16 dimensions total). Tests whether graph message passing adds value over the existing scalar heuristic.

---

## 8. Statistical Significance & Reporting

- **Evaluation Metrics:**
  - Macro-Averaged $F_1$, Macro-Precision, Macro-Recall, Accuracy.
  - Per-class confusion matrices ($3 \times 3$).
  - NDCG@10, NDCG@20, and Spearman's $\rho$ against expert rank order.
- **Confidence Intervals:** 1,000-iteration bootstrap resampling for 95% Confidence Intervals.
- **Paired Permutation Testing:** 1,000 paired randomized permutations testing $H_0: \text{Metric}_{\text{GATv2}} = \text{Metric}_{\text{Baseline}}$.
- **Missing Prediction Policy:** Missing predictions are scored as errors (penalized), never omitted from metric denominators.

---

## 9. Items Requiring Project Guide Sign-Off

Before freezing this protocol:

1. **Protocol Partition Selection**: Confirm approval of the Language-Balanced Inductive Split (Protocol A) versus 8-fold Leave-One-Repository-Out Cross-Validation (Protocol C).
2. **AHP-Lite Adoption**: Approve the use of the 21-item AHP pairwise survey to replace ad-hoc initial weights with empirical expert-derived weights.
3. **Participant Disclosures**: Confirm departmental guidelines regarding ethics oversight / participant consent for external expert reviews.
4. **Temporary Development Phase**: Concurrence that the synthetic dry-run pipeline is approved exclusively for software integration verification until genuine experts complete their reviews.
