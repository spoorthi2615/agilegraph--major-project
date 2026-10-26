# GATv2 Architecture and Empirical Evaluation

## 1. Status and Provenance
- **Scientific Framing**: Weak-label distillation evaluated; expert-label validation blocked.
- **Model Infrastructure**: Implemented via `HeteroGATv2` with dynamic projection and residual connections (`backend/src/ml/gatv2.py`).
- **Corpus Evaluation**: Evaluated across all 8 pinned canonical benchmark repositories ($N = 520$ file nodes).
- **Cross-Validation Scheme**: 8-Fold Leave-One-Project-Out (LOPO) cross-validation across heterogeneous codebases (Go, Java, Python).
- **Artifacts Saved**: `backend/dataset/artifacts/gatv2_evaluation_results.json`.

---

## 2. Architecture Design
The AgileGraph model utilizes a Heterogeneous Graph Attention Network (GATv2) built with PyTorch Geometric (`torch_geometric`). The `create_hetero_gatv2` function operates directly on heterogeneous graph metadata, providing:
- Per-node-type linear projection to `hidden_channels` ($32$).
- Multi-head attention across typed edges using `GATv2Conv` wrapped in `HeteroConv` with residual fallbacks.
- Final multi-class linear classification head for 3 risk categories:
  - Class 0: **LOW** ($< 0.30$)
  - Class 1: **MEDIUM** ($[0.30, 0.60)$)
  - Class 2: **HIGH** ($\ge 0.60$)

---

## 3. Node Features and Target-Generating Information

### 3.1 14-Dimensional Feature Vector
Node features for file nodes strictly contain 14 dimensions:
- **7 Factor Values**: `data_sensitivity`, `asset_criticality`, `internet_exposure`, `crypto_weakness`, `cve_risk`, `library_centrality`, `migration_difficulty`.
- **7 Observation Masks**: $0.0$ if the factor is observed, $1.0$ if missing.

### 3.2 Methodological Distinction: Scalar Leakage vs. Formula Approximation
To maintain absolute scientific precision, AgileGraph distinguishes three levels of target exposure:
1. **Direct Inclusion of the Target-Generating Composite Score (Direct Leakage)**: Including the continuous scalar `base_risk` directly in the feature vector (15-dim). This is strictly prohibited by default (`FeatureConfig.include_base_risk=False`) because it allows the model to learn a trivial scalar threshold shortcut.
2. **Learning from Component Variables Used to Calculate the Target (Formula Approximation)**: The 14-dimensional feature vector excludes `base_risk`, but contains the 7 constituent factors and 7 missingness masks that deterministically generate `base_risk`. Consequently, the 14-dimensional model is **not** an independent predictor of real-world cryptographic risk; it is an empirical function approximator learning to emulate the deterministic heuristic weighting formula from its component inputs.
3. **Genuine Prediction Against Independently Obtained Outcomes**: True predictive validity would require testing against external, independently verified outcomes (e.g., real-world post-quantum breach incidents or expert consensus migration logs). In the absence of an independent ground truth, all ML evaluation metrics describe fidelity in approximating the weak-supervision heuristic rules.

---

## 4. Empirical Evaluation Results

> [!IMPORTANT]
> **Scientific Framing: Weak-Label Distillation Evaluated | Expert-Label Validation Blocked**
> - **Weak-Label Distillation (Evaluated)**: The Heterogeneous GATv2 model and comparative baselines are fully evaluated on the 8 pinned benchmark repositories ($N = 520$ file nodes) under 8-fold Leave-One-Project-Out (LOPO) cross-validation. These results characterize representation distillation and agreement with the heuristic labeling procedure under cross-repository domain shift.
> - **Expert-Label Validation (Blocked)**: Validation against independent human expert consensus labels or confirmed real-world cryptanalytic exploitation incidents is blocked due to the absence of certified expert-annotated datasets. No independent real-world predictive validity is claimed beyond weak-supervision distillation.

### 4.1 Leave-One-Project-Out (LOPO) Controlled Cross-Validation ($N = 520$ Files)
To prevent intra-repository data leakage, each fold held out exactly one repository as the test set while training strictly on the remaining seven. All model architectures and controls were evaluated on identical held-out folds using identical target labels and identical preprocessing.

Both the **pooled sample accuracy** (weighting all 520 files equally) and the **unweighted fold mean** (treating each repository fold equally regardless of file count) are reported below:

| Model / Control Architecture | Pooled Sample Accuracy (95% CI) | Unweighted Fold Mean Acc (Std Dev) | Balanced Acc | Macro-F1 (95% CI) | HIGH Recall (Class 2) | HIGH Precision (Class 2) | Role & Scientific Finding |
|---|---|---|---|---|---|---|---|
| **Non-Graph Feature-Only MLP** | **81.92%** [78.85%, 85.00%] | 63.13% (± 41.09%) | **72.05%** | **0.7073** [0.6647, 0.7499] | **27.18%** (28/103) | **90.32%** (28/31) | **Feature-only baseline**: Local node factors generalize consistently across repositories. |
| **Randomized-Edge GATv2 Control** | **78.85%** [75.19%, 82.12%] | 74.35% (± 23.44%) | **75.24%** | **0.7067** [0.6606, 0.7464] | **97.09%** (100/103) | **54.64%** (100/183) | **Graph-structure control**: Degree-preserving edge randomization removes semantic topology. |
| **Heterogeneous GATv2 (14-dim)** | **66.73%** [62.69%, 70.58%] | **72.44%** (± 31.26%) | **54.18%** | **0.5560** [0.5060, 0.6049] | **27.18%** (28/103) | **90.32%** (28/31) | **Proposed GNN**: Subject to cross-codebase graph structural shift across languages. |
| **GATv2 with Target Leakage (15-dim)**| *96.73%* [95.19%, 98.08%] | 85.74% (± 22.59%) | *96.30%* | *0.9645* [0.9456, 0.9793] | *97.09%* (100/103) | *97.09%* (100/103) | **Ablation check**: Demonstrates +30.00% artificial boost when scalar label source is exposed. |
| **Static Rule Baseline** | 42.12% | 46.88% (± 24.11%) | 43.14% | 0.4119 | 30.10% (31/103) | 35.63% (31/87) | Rule-based heuristic matching on primary weakness. |
| **Majority Class Baseline** | 22.69% | 22.69% (± 0.00%) | 14.95% | 0.1321 | 0.00% (0/103) | 0.00% (0/0) | Statistical majority floor across folds. |
| **Heuristic Teacher Baseline** | *100.0%* | *100.0%* (± 0.00%) | *100.0%* | *1.0000* | *100.0%* | *100.0%* | Tautological upper ceiling (source of weak labels). |

#### Multi-Seed Stability Analysis (Seeds = 42, 100, 2026 across all 8 folds)
While the primary benchmark table above reports the canonical Seed 42 run ($N = 520$ pooled nodes), all architectures were additionally evaluated across multiple random seeds to evaluate initialization stability. Both the primary seed and this multi-seed analysis are directly reproduced via `python scripts/run_gatv2_evaluation.py --multi-seed`:
- **Non-Graph MLP**: Accuracy = **$81.22\% \pm 0.68\%$** (pop. $\pm 0.55\%$) | Macro-F1 = **$0.7022 \pm 0.0049$** (pop. $\pm 0.0040$). The non-graph baseline is exceptionally stable across initializations.
- **Heterogeneous GATv2**: Accuracy = **$71.60\% \pm 7.46\%$** (pop. $\pm 6.09\%$) | Macro-F1 = **$0.6163 \pm 0.0991$** (pop. $\pm 0.0810$). The GNN exhibits substantial sensitivity to parameter initialization on cross-codebase graphs.
- **Randomized-Edge GATv2**: Accuracy = **$77.82\% \pm 1.95\%$** (pop. $\pm 1.59\%$) | Macro-F1 = **$0.6934 \pm 0.0321$** (pop. $\pm 0.0262$).
- **GATv2 with Target Leakage**: Accuracy = **$96.86\% \pm 0.23\%$** (pop. $\pm 0.19\%$) | Macro-F1 = **$0.9660 \pm 0.0026$** (pop. $\pm 0.0021$).

#### Clarification on Confidence Intervals and Resampling Units
The 95% bootstrap confidence intervals ($B = 1000$ iterations) are computed by resampling **individual file predictions pooled across the 520 evaluated nodes**.
- **Descriptive within-sample uncertainty**: These intervals describe the sampling variability of the aggregate 520-file test sample under the fixed LOPO evaluation protocol.
- **Not project-level generalization uncertainty**: These intervals do **not** represent cluster-robust project-level generalization uncertainty. Software repositories represent natural clusters of widely disparate sizes (1 to 178 files) with overlapping LOPO training sets.
- **Limitations of Inference with $K=8$ Projects**: A project-level cluster bootstrap with only 8 independent repositories is statistically unviable and volatile (e.g., $34.4\%$ of cluster bootstrap resamples would omit the largest repository `python_cryptography` entirely). True project-to-project variability is properly quantified by the unweighted fold-level standard deviations reported above.

---

### 4.2 Aggregate Confusion Matrices ($N = 520$ Files)

#### Heterogeneous GATv2 (Genuine 14-dim, Seed 42):
$$\begin{pmatrix} 
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{True LOW (0)} & \mathbf{262} & 12 & 2 \\
\text{True MED (1)} & 83 & \mathbf{57} & 1 \\
\text{True HIGH (2)} & 26 & 49 & \mathbf{28}
\end{pmatrix}$$
- **Class 0 (LOW, $N=276$)**: Precision = $70.6\%$, Recall = **$94.9\%$**, F1 = **$0.810$**
- **Class 1 (MED, $N=141$)**: Precision = $48.3\%$, Recall = **$40.4\%$**, F1 = **$0.440$**
- **Class 2 (HIGH, $N=103$)**: Precision = **$90.3\%$**, Recall = **$27.2\%$**, F1 = **$0.418$**

#### Non-Graph Feature-Only MLP (14-dim, Seed 42):
$$\begin{pmatrix} 
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{True LOW (0)} & \mathbf{269} & 7 & 0 \\
\text{True MED (1)} & 9 & \mathbf{129} & 3 \\
\text{True HIGH (2)} & 0 & 75 & \mathbf{28}
\end{pmatrix}$$
- **Class 0 (LOW, $N=276$)**: Precision = $96.8\%$, Recall = **$97.5\%$**, F1 = **$0.971$**
- **Class 1 (MED, $N=141$)**: Precision = $61.1\%$, Recall = **$91.5\%$**, F1 = **$0.733$**
- **Class 2 (HIGH, $N=103$)**: Precision = **$90.3\%$**, Recall = **$27.2\%$**, F1 = **$0.418$**

---

### 4.3 Continuous Score Rank Correlations
We evaluate rank monotonicity across all $N = 520$ file nodes using both Spearman's rank correlation ($\rho$) and Kendall's rank correlation ($\tau$):

1. **Continuous Heuristic Composite Score vs. Discrete Risk Tiers (0, 1, 2)**:
   - **Spearman $\rho$**: **$0.9090$** ($p = 5.05 \times 10^{-199}$)
   - **Kendall $\tau$**: **$0.7950$** ($p = 1.19 \times 10^{-115}$)
   - *Interpretation*: Confirms that the discrete tier thresholds preserve strong monotonic ordering over the continuous 7-factor composite score across the entire benchmark dataset.

2. **Out-of-Fold Continuous GATv2 Predictions vs. Continuous Heuristic Score**:
   - **Spearman $\rho$**: **$0.8038$** ($p = 6.07 \times 10^{-119}$)
   - **Kendall $\tau$**: **$0.6063$** ($p = 1.65 \times 10^{-88}$)

3. **Out-of-Fold Continuous MLP Predictions vs. Continuous Heuristic Score**:
   - **Spearman $\rho$**: **$0.8207$** ($p = 4.88 \times 10^{-128}$)
   - **Kendall $\tau$**: **$0.6471$** ($p = 2.18 \times 10^{-100}$)

*Methodological Caveat on P-values*: The nominal p-values assume independent observations across all 520 nodes. Because file nodes are clustered within 8 software projects, these statistics describe within-corpus score-tier monotonicity rather than cluster-robust cross-project hypothesis tests. Furthermore, strong rank agreement demonstrates fidelity in approximating the heuristic ranking function, **not** independent real-world risk validity.

---

### 4.4 Verification of Randomized-Edge Control Invariants and High Recall Degeneracy

#### Graph Property Invariants
The randomized-edge control function (`shuffle_edges()`) randomly permutes destination node indices independently for each edge relation. Direct mathematical and empirical verification confirms:
- **Edge Count Preservation**: Preserves the exact edge count for every relation triplet.
- **Degree Distribution Preservation**: Preserves the 1D out-degree distribution of source nodes and the 1D in-degree distribution of destination nodes for each bipartite edge type.
- **Topological Disruption**: Destroys high-order semantic relational topology (e.g., call chains, dependency paths, and cross-type neighborhoods).
- **Seed Determinism**: Fully reproducible under a fixed pseudo-random number generator seed.

#### Investigation of the 97.09% HIGH-Risk Recall in the Randomized-Edge Control
The randomized-edge control achieves $97.09\%$ HIGH recall ($100/103$), whereas genuine GATv2 and MLP achieve $27.18\%$ ($28/103$). A thorough fold-level inspection revealed the exact optimization degeneracy:
1. **Extreme Cross-Fold Imbalance**: In Fold 7 (`python_cryptography`), the training set contains only 4 HIGH files out of 342 ($1.1\%$), leading to an extreme inverse-frequency class weight of $28.5$ for HIGH ($68.5\times$ that of LOW).
2. **Loss Function Incentivization Under Noise**: Under randomized message passing, the network receives corrupted, non-informative structural signals. To minimize the heavily weighted loss on HIGH examples, the unconstrained model collapses to overpredicting HIGH.
3. **Overprediction in Fold 7**: The randomized model predicts HIGH for **175 out of the 178 files** in Fold 7.
4. **Precision Collapse**: While this blanket overprediction catches $99$ of the $99$ True HIGH files in Fold 7, it simultaneously misclassifies **$76$ of the $77$ True MEDIUM files as HIGH**.
5. **Net Result**: The randomized model's HIGH recall is an artifact of class-weight sensitivity under noise, resulting in a **collapse of HIGH precision to $54.64\%$ ($100/183$)**, compared to **$90.32\%$ ($28/31$)** for both genuine GATv2 and the Non-Graph MLP.

---

## 5. Controlled Target Leakage Ablation

| Configuration | Input Dim | Evaluation Mode | Pooled Accuracy | Unweighted Fold Mean Acc | Balanced Acc | Macro-F1 | Finding |
|---|---|---|---|---|---|---|---|
| **WITHOUT_BASE_RISK (Genuine)** | 14 | Cross-Repo LOPO | **66.73%** | 72.44% | **54.18%** | **0.5560** | Evaluated without continuous target leakage |
| **WITH_BASE_RISK (Target Leaked)** | 15 | Cross-Repo LOPO | **96.73%** | 85.74% | **96.30%** | **0.9645** | **+30.00% Artificial Leakage Boost** |

When the continuous scalar `base_risk` is appended to the node feature vector, cross-repository accuracy jumps from 66.73% to 96.73% (+30.00%). This demonstrates that models easily learn a scalar shortcut if target leakage is not strictly prevented.

---

## 6. Critical Scientific Analysis & Honest Interpretation

### 6.1 Why the Non-Graph Baseline Outperforms GATv2
Under Leave-One-Project-Out evaluation across heterogeneous codebases (Go, Java, Python), the Non-Graph Feature-Only MLP achieves **81.92% pooled accuracy** (Macro-F1 0.7073; multi-seed mean $81.22\% \pm 0.55\%$), outperforming GATv2's **66.73%** (Macro-F1 0.5560; multi-seed mean $71.60\% \pm 6.09\%$).
- **Hypothesis — Cross-Codebase Graph Structural Shift**: Graph topology varies significantly across programming languages, project architectures, and framework conventions. A GNN's multi-head attention over heterogeneous edge types (`CALLS`, `IMPORTS`, `CONTAINS`) is sensitive to repository-specific topological structures that do not transfer directly to a different project.
- **Local Feature Stability**: In contrast, local node security factors (e.g., algorithmic weakness, CVE presence, internet exposure, asset criticality) carry consistent semantic meaning regardless of repository structure.
- **Academic Conclusion**: The empirical evidence does **not** demonstrate that graph topology provides a predictive benefit over local feature analysis for weak-label tier imitation across heterogeneous repositories. This negative result is reported honestly as an essential scientific finding.

### 6.2 High-Risk Recall is 27.2% Across Both Models
Both GATv2 and the Non-Graph MLP achieve identical HIGH recall of **27.18% (28/103)**. This is directly driven by class distribution concentration:
- **99 of the 103 High-risk files in the entire corpus reside in `python_cryptography`**.
- In the remaining 7 repositories, High-risk files are nearly absent (only 4 files across 7 projects).
- When `python_cryptography` is held out during LOPO fold 7, the training set contains only 4 High-risk examples out of 342 files ($1.1\%$), starving both models of high-risk training signals.

### 6.3 Architectural Safeguards and Product Behavior
Because a 27.2% recall on High-risk code cannot be trusted as a standalone triage filter in a security tool, AgileGraph enforces a strict architectural boundary:
1. **Deterministic Scanners as Authoritative Ground**: Deterministic static AST/regex scanners independently identify and catalog all cryptographic weaknesses. Known quantum-vulnerable primitives (e.g., RSA, DSA, ECC) are **never** suppressed or bypassed by the GNN.
2. **GNN as an Experimental Prototype Layer**: In production scans (`backend/src/pipeline/runner.py`), the system executes 100% deterministically using the AST scanners and the 7-factor heuristic engine. While weak-label distillation has been evaluated across the benchmark corpus, expert-label validation remains blocked; hence the PyTorch GATv2 model is isolated as an architectural prototype (`ml_status: ARCHITECTURAL_PROTOTYPE`).
3. **Graph Utility vs. GNN Classification**: The typed property graph remains foundational for interactive visualization, call-chain dependency tracing, blast-radius analysis, and migration planning, even though GATv2 message passing does not improve discrete classification over local feature vectors.
