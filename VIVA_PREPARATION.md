# AgileGraph — Viva Preparation & Examiner Q&A Guide

**Target Audience**: Project defense panel, external examiners, cybersecurity evaluators, machine learning reviewers.

---

## 1. High-Yield Examiner Questions & Model Answers

### Q1: Why did your original heuristic (V1) achieve only a 0.3225 Macro-F1 against human experts? Did the system fail?
**Model Answer**:
> "No, this was not a failure of implementation; it was one of our most important scientific discoveries.
> Human domain experts evaluate cryptographic risk primarily on **intrinsic mathematical hardness**—specifically whether an algorithm is broken by Shor's algorithm (such as RSA or ECDSA). When experts see an RSA key generation helper or test vector, they immediately rate it as HIGH risk.
> In contrast, our baseline 7-factor heuristic engine evaluates **contextual and environmental risk**. It balances algorithm weakness with internet exposure, data sensitivity, call reachability, and CVE presence. In non-production test fixtures and internal helper abstractions, exposure and data sensitivity are low, dampening the composite score from HIGH into MEDIUM or LOW.
> When our heuristic does flag an asset as HIGH, it is confirmed HIGH by experts in **80.65%** of cases. The discrepancy is an authentic divergence between intrinsic cryptanalytic threat and contextual deployment risk."

### Q2: How did Heuristic V2 address this divergence, and how did you prevent data leakage during calibration?
**Model Answer**:
> "We addressed this through two independently ablated components:
> 1. **Data-Aware Threshold Calibration**: We observed that assets with sparse metadata had compressed scores. We calibrated class cutoffs conditioned on available evidence.
> 2. **Semantic Graph Weakness Inheritance**: Abstract wrappers and key builders often do not contain concrete cipher calls, but import libraries that do. Using our typed property graph, we propagated cryptographic weakness across verified `IMPORTS` edges with an attenuation factor ($\alpha = 0.55$).
> Crucially, to prevent data leakage, we evaluated this under **Leave-One-Repository-Out (LORO) cross-validation across 7 repositories**. In every fold, optimal cutoffs were calculated strictly on 6 training repositories and applied blindly to the 7th held-out repository. Across all 160 held-out test predictions, out-of-fold Macro-F1 increased from **0.3225 to 0.7312**, and HIGH recall rose from **31.25% to 91.25%**."

### Q3: Why did you keep V1 as the default if V2 performs so much better on expert consensus?
**Model Answer**:
> "In high-assurance security engineering, stability, explainability, and operational transparency take precedence over uncalibrated updates.
> Heuristic V1 has high specificity on non-cryptographic assets ($\text{Recall}_{\text{LOW}} = 89.66\%$). In V2, because structural weakness propagates across imports, test suites that import key builders inherit an attenuated risk score, causing LOW recall to drop to $48.28\%$.
> We adopted **Option B: Dual-Engine Architecture**. V1 remains the stable, permanent default for baseline operational compliance. V2 is exposed as an explicit, selectable experimental engine for security teams who want aggressive, discovery-focused triage. Both engines report provenance explicitly in every API payload and UI view."

### Q4: What is Experiment 3 (Candidate V3-Alpha), and why did you not promote it to production?
**Model Answer**:
> "Experiment 3 investigated the root cause of V2's LOW recall drop. We observed that V2 propagated weakness from both asymmetric and symmetric libraries. However, under post-quantum principles:
> - Shor's algorithm completely breaks asymmetric cryptography (RSA, ECC) in polynomial time.
> - Grover's algorithm only provides quadratic speedup on symmetric ciphers (AES-256) and hashing (SHA-384/512), meaning they remain post-quantum secure.
> By restricting graph weakness propagation strictly to asymmetric abstractions, Experiment 3 achieved **0.8172 Macro-F1** and restored LOW recall to **75.86%**.
> However, as rigorous researchers, we recognized that the keyword criteria for Experiment 3 were designed after inspecting misclassified assets in our evaluation corpus. Promoting it to production would represent **test-set-informed method development**. We therefore documented Experiment 3 strictly as a **post-hoc exploratory asymmetric-specific propagation ablation**, keeping it out of runtime production until independent external validation on a fresh repository corpus can be performed."

### Q5: How did you compute inter-rater agreement for your 4 experts, and how were conflicts resolved?
**Model Answer**:
> "We collected independent evaluations across 160 repository-scoped assets. Expert 4 excluded 6 assets due to insufficient context, leaving 154 assets with full 4-way evaluation.
> We evaluated agreement using two statistical tests:
> 1. **Fleiss' Generalized Multi-Rater Kappa**: $\kappa_{\text{Fleiss}} = 0.7791$, demonstrating substantial inter-annotator agreement across all 4 reviewers simultaneously.
> 2. **Mean Pairwise Linear Weighted Cohen's Kappa**: $\bar{\kappa} = 0.8167$, showing almost perfect pairwise agreement with penalty scaling proportional to ordinal distance (LOW vs HIGH is penalized more than LOW vs MEDIUM).
> For adjudication:
> - 117 assets had unanimous agreement ($73.1\%$).
> - 32 assets had majority agreement ($20.0\%$).
> - 11 ties were resolved by taking the conservative, security-conscious ceiling."

### Q6: What is the purpose of GATv2 and GNNExplainer if you already have the heuristic engine?
**Model Answer**:
> "The GATv2 model serves as a **weak-supervision representation learning engine**. It explores whether a Graph Attention Network can distill the complex, multi-factor risk topology directly from code property graphs under domain shift.
> Evaluated under 8-fold Leave-One-Project-Out cross-validation across 520 file nodes, GATv2 achieves high distillation fidelity.
> **GNNExplainer** provides local post-hoc interpretability. For any given file, it identifies the most influential edge connections (e.g., an `IMPORTS` edge to an unapproved library) and feature dimensions that drove the classification, making the graph's decisions transparent to human security auditors."

---

## 2. Key Statistical Formulas & Definitions Reference

Be prepared to write or explain these formulas on a whiteboard:

### 1. The Heuristic Formula:
$$\text{base\_risk} = \sum_{i=1}^7 w_i \cdot f_i \quad \text{where } \sum_{i=1}^7 w_i = 1.0$$
If evidence is missing under `RENORMALIZE`:
$$w_i' = \frac{w_i}{\sum_{j \in \mathcal{O}} w_j} \quad \text{for observed factors } \mathcal{O}$$

### 2. Mosca Urgency Index:
$$U = \frac{X + Y}{Z}$$
- $X$: Data confidentiality shelf-life.
- $Y$: Migration execution timeline.
- $Z$: Timeline until a Cryptanalytically Relevant Quantum Computer (CRQC).
- Decision Boundary: $X + Y > Z \iff U > 1.0 \implies \text{AT\_RISK}$.

### 3. Linear Weighted Cohen's Kappa:
$$\kappa_w = 1 - \frac{\sum_{i,j} w_{ij} O_{ij}}{\sum_{i,j} w_{ij} E_{ij}} \quad \text{where } w_{ij} = \frac{|i - j|}{k - 1}$$

### 4. Graph Weakness Propagation (V2):
$$\text{propagated\_weakness}(u) = \alpha \cdot \max_{v \in \mathcal{N}_{\text{crypto}}(u)} \text{weakness}(v)$$
where $\alpha = 0.55$, followed by updating composite risk:
$$\text{effective\_risk}(u) = \max(\text{base\_risk}(u), \text{propagated\_weakness}(u))$$

---

## 3. Defense Presentation Tips

1. **Be Proud of the Low Initial F1 (0.3225)**: Panels respect honest empirical science. Explain that finding this divergence between expert perception and static formulas is exactly why graph propagation (V2) was necessary.
2. **Emphasize Methodological Rigor**: Stress that all parameters were fitted under **Leave-One-Repository-Out (LORO)** cross-validation, meaning models were tested on codebases they had never seen during threshold fitting.
3. **Point to Working Artifacts**: If questioned on reproducibility, highlight that all results are serialized in JSON artifacts (`expert_validation_report.json`, `heuristic_v2_experiment_results.json`) and covered by 439 passing automated unit/integration tests.

