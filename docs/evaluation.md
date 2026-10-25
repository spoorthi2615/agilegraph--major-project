# GATv2 Architecture and Empirical Evaluation

## 1. Status and Provenance
- **Model Infrastructure**: Implemented via `HeteroGATv2` with dynamic projection and residual connections.
- **Corpus Evaluation**: Evaluated across all 8 canonical benchmark repositories ($N = 520$ file nodes).
- **Cross-Validation Scheme**: 8-Fold Leave-One-Project-Out (LOPO) cross-validation.
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

## 3. Node Features and Target Leakage Prevention

### 3.1 14-Dimensional Feature Vector
Node features for file nodes strictly contain 14 dimensions:
- **7 Factor Values**: `data_sensitivity`, `asset_criticality`, `internet_exposure`, `crypto_weakness`, `cve_risk`, `library_centrality`, `migration_difficulty`.
- **7 Observation Masks**: $0.0$ if the factor is observed, $1.0$ if missing.

### 3.2 Target Leakage Safeguard
By default, `FeatureConfig.include_base_risk=False`. Continuous `base_risk` is **strictly excluded** from node features. The model is forced to learn structural relationships (`IMPORTS`, `CONTAINS`, `CALLS`, `DEPENDS_ON`) and constituent factors rather than performing a scalar shortcut.

---

## 4. Empirical Evaluation Results

### 4.1 Leave-One-Project-Out (LOPO) Cross-Validation ($N = 520$ Files)
To prevent intra-repository data leakage, each fold held out exactly one repository as the test set while training strictly on the remaining seven:

| Metric | GATv2 (LOPO Out-of-Fold) | Majority Baseline | Corrected Static Rule Baseline | Heuristic Teacher Baseline |
|---|---|---|---|---|
| **Overall Accuracy** | **66.73%** | 22.69% | 42.12% | *100.0%* |
| **Balanced Accuracy** | **54.18%** | 14.95% | 43.14% | *100.0%* |
| **Macro-F1** | **0.5560** | 0.1321 | 0.4119 | *1.0000* |
| **Macro-Precision** | **69.75%** | 11.84% | 40.05% | *100.0%* |
| **Macro-Recall** | **54.18%** | 14.95% | 43.14% | *100.0%* |

*Note on Static Rule Baseline*: An audit identified an earlier feature-index error in `run_gatv2_evaluation.py` (querying index 0 instead of index 3 for `crypto_weakness`). The corrected metric is **42.12% accuracy and 0.4119 macro-F1** (not the previously reported 40.38% and 0.3022).

*Note on Heuristic Teacher Baseline*: The 100.0% concordance is the expected agreement with its own weak supervision formula, serving as the distillation upper bound.

### 4.2 Aggregate Confusion Matrix ($N = 520$ Files)

$$\begin{pmatrix} 
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{True LOW (0)} & \mathbf{262} & 12 & 2 \\
\text{True MED (1)} & 83 & \mathbf{57} & 1 \\
\text{True HIGH (2)} & 26 & 49 & \mathbf{28}
\end{pmatrix}$$

- **Class 0 (LOW, $N=276$)**: Precision = $70.6\%$, Recall = **$94.9\%$**, F1 = **$0.810$**
- **Class 1 (MED, $N=141$)**: Precision = $48.3\%$, Recall = **$40.4\%$**, F1 = **$0.440$**
- **Class 2 (HIGH, $N=103$)**: Precision = **$90.3\%$**, Recall = **$27.2\%$**, F1 = **$0.418$**

---

## 5. Controlled Target Leakage Ablation

| Configuration | Input Dim | Evaluation Mode | Accuracy | Balanced Acc | Macro-F1 | Finding |
|---|---|---|---|---|---|---|
| **WITHOUT_BASE_RISK (Genuine)** | 14 | Cross-Repo LOPO | **66.73%** | **54.18%** | **0.5560** | Genuine structural generalization |
| **WITH_BASE_RISK (Target Leaked)** | 15 | Cross-Repo LOPO | **83.08%** | **73.23%** | **0.7185** | **+16.35% Artificial Leakage Boost** |
| *Intra-Repo Resubstitution* | 14 vs 15 | Train Set (`python_cryptography`) | 98.31% | 66.23% | 0.6595 | Both saturate on training examples |

*Audit Finding*: Earlier reports noted identical 98.31% performance because the ablation evaluated on training examples of `python_cryptography` ($N=178$), where 15k parameters memorized the 178 nodes in both cases. Testing on out-of-fold cross-codebase LOPO clearly demonstrates that target leakage inflates accuracy by $+16.35\%$.

---

## 6. Critical Scientific Limitations & System Safeguards

### 6.1 High-Risk Recall is 27.2%
The model identified 28 of 103 High-risk files. This is directly tied to cross-codebase domain concentration: **99 of the 103 High-risk files in the entire corpus reside in `python_cryptography`**. When `python_cryptography` is held out, the training set contains only 4 High-risk examples ($1.1\%$), starving the model of high-risk signals.

### 6.2 Architectural Safeguard
Because a 27.2% recall on High-risk code cannot be trusted as a standalone filter, AgileGraph enforces a strict safeguard:
- **GNN as an Enrichment & Prioritization Layer**: The GNN provides graph-structural representation and learned risk ranking.
- **Deterministic Scanners as Authoritative Ground**: Deterministic AST scanners and heuristic rules independently compute and report all detected cryptographic weaknesses. Known quantum-vulnerable primitives (e.g. RSA, DSA) are **never** suppressed or bypassed by the GNN.

### 6.3 Weak Supervision Caveat
The discrete labels were derived from AgileGraph's heuristic risk formula. The experiment demonstrates representation distillation—how well the GNN reproduces multi-factor risk categorization from graph structure—not independent predictive validity against real-world post-quantum exploits or measured migration labor.
