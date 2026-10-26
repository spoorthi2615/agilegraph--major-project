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

### 3.3 Mandatory Scientific Caveat: Distillation Agreement vs. Empirical Validation
To prevent academic overclaiming:
1. **Fidelity to Heuristic Priors, Not Real Risk Prediction**:
   All reported classification and rank metrics (Accuracy, Macro-F1, Balanced Accuracy, Spearman $\rho$, Kendall $\tau$) measure strictly the **statistical agreement between the neural representations and the deterministic heuristic engine**. They demonstrate *representation distillation fidelity* (whether graph message-passing or multi-layer perceptrons approximate the piecewise-linear heuristic mapping across unseen codebases). They do **NOT** constitute empirical validation of real-world post-quantum risk, cryptanalytic exploitability, or ground-truth vulnerability correctness. If the heuristic engine contains systematic biases, an accurate model simply reproduces those biases.
2. **Elimination of Baseline Input Leakage**:
   Early evaluation scripts introduced baseline circularity by allowing the static rule baseline to threshold `crypto_weakness` and `library_centrality` (which are direct inputs to the heuristic target label). This circularity was completely excised: the rule baseline in `src/ml/baselines.py` operates strictly as an independent AST regex matcher on raw scanner findings against three PQC categories (Classically Broken, Quantum Vulnerable, Quantum Resistant), without access to any heuristic factor values or labels.

---

## 4. Empirical Evaluation Results

> [!IMPORTANT]
> **Scientific Framing: Weak-Label Distillation Evaluated | Expert-Label Validation Blocked**
> - **Evolution from Early Scaffolding**: In early architectural scaffolding, model training was deferred. In the finalized implementation, the Heterogeneous GATv2 model and all baselines **ARE fully trained to convergence with early stopping** across all 8 benchmark repositories ($N = 520$ file nodes) under 8-fold Leave-One-Project-Out (LOPO) cross-validation.
> - **Weak-Label Distillation (Evaluated)**: Target labels are derived from the deterministic 7-factor heuristic risk engine. These empirical results characterize *representation distillation* (whether GNNs or MLPs can learn to distill the multi-factor risk topology from code property graphs under cross-repository domain shift).
> - **Expert-Label Validation (Blocked)**: Validation against *independent external human cryptographer consensus panels* or *confirmed real-world cryptanalytic exploitation incidents* remains strictly **blocked** due to the absence of certified expert-annotated datasets in the open literature. No independent real-world predictive validity is claimed beyond weak-supervision distillation.
> - **Production Runtime Separation**: In live production scans, GATv2 is isolated as an architectural prototype (`ml_status: ARCHITECTURAL_PROTOTYPE`) so it cannot alter or suppress deterministic AST scanner findings.

### 4.1 Leave-One-Project-Out (LOPO) Controlled Cross-Validation ($N = 520$ Files, Trained to Convergence)
To prevent intra-repository data leakage, each fold held out exactly one repository as the test set while training strictly on the remaining seven. All model architectures and controls were trained to convergence using inner stratified validation splits and patience-based early stopping (max 300 epochs, patience 25 for GATv2, patience 30 for MLP) on identical held-out folds using identical target labels and identical preprocessing.

Both the **pooled sample accuracy** (weighting all 520 files equally) and the **unweighted fold mean** (treating each repository fold equally regardless of file count) are reported below:

| Model / Control Architecture | Pooled Sample Accuracy (95% CI) | Unweighted Fold Mean Acc (Std Dev) | Balanced Acc | Macro-F1 (95% CI) | HIGH Recall (Class 2) | HIGH Precision (Class 2) | Role & Empirical Finding |
|---|---|---|---|---|---|---|---|
| **Non-Graph Feature-Only MLP** | **98.08%** [96.73%, 99.23%] | 84.35% (± 34.84%) | **98.24%** | **0.9802** [0.9655, 0.9928] | **99.03%** (102/103) | **99.03%** (102/103) | **Feature baseline**: Directly approximates piecewise heuristic formula from local factors. |
| **Heterogeneous GATv2 (14-dim)** | **83.08%** [80.00%, 86.00%] | **89.38%** (± 14.84%) | **73.12%** | **0.7176** [0.6738, 0.7599] | **27.18%** (28/103) | **96.55%** (28/29) | **GNN prototype**: Message passing; starved of HIGH files on Fold 7 (trained on 4 HIGH files). |
| **Randomized-Edge GATv2 Control** | **74.81%** [71.00%, 78.30%] | 64.92% (± 30.25%) | **71.66%** | **0.6629** [0.6195, 0.7012] | **97.09%** (100/103) | **43.10%** (100/232) | **Graph control**: Preserves degree distribution; noise causes Fold-7 HIGH overprediction. |
| **GATv2 with Target Leakage (15-dim)**| 81.92% [78.60%, 85.00%] | 88.78% (± 15.01%) | 72.91% | 0.7167 [0.6730, 0.7613] | 29.13% (30/103) | 96.77% (30/31) | **Ablation check**: Evaluated with scalar `base_risk` appended to node feature vector. |
| **Static Rule Baseline** | 52.12% | 49.14% (± 35.12%) | 38.61% | 0.3567 | 24.27% (25/103) | 37.31% (25/67) | Independent AST regex baseline: matches raw scanner findings against PQC categories without heuristic factor inputs. |
| **Majority Class Baseline** | 22.69% | 22.69% (± 0.00%) | 14.95% | 0.1321 | 0.00% (0/103) | 0.00% (0/0) | Statistical majority floor across folds. |
| **Heuristic Teacher Baseline** | *100.0%* | *100.0%* (± 0.00%) | *100.0%* | *1.0000* | *100.0%* | *100.0%* | Tautological upper ceiling (source of weak labels). |

#### Complementary Benchmark: Stratified 5-Fold Cross-Validation ($N = 520$ Files)
To test whether the architectures can accurately classify the HIGH-risk tier when training folds are provided with representative HIGH examples (overcoming Fold-7 starvation), all 520 nodes were evaluated under Stratified 5-Fold Cross-Validation:

| Model / Control Architecture | Accuracy | Macro-F1 | HIGH Recall (Class 2) | HIGH Precision (Class 2) | Role & Empirical Finding |
|---|---|---|---|---|---|
| **Non-Graph Feature-Only MLP** | **97.31%** | **0.9709** | **97.09%** (100/103) | **99.01%** (100/101) | Directly approximates the 7-factor piecewise formula. |
| **Heterogeneous GATv2 (14-dim)** | **84.81%** | **0.8005** | **74.76%** (77/103) | **70.00%** (77/110) | Graph attention message passing with representative HIGH training signal. |
| **Randomized-Edge GATv2 Control** | **75.19%** | **0.6770** | **65.05%** (67/103) | **52.34%** (67/128) | Permuted topology; noise degrades accuracy by 9.6% and precision by 17.7%. |

#### Multi-Seed Stability Analysis (Seeds = 42, 100, 2026 across all 8 folds)
While the primary benchmark table above reports the canonical Seed 42 run ($N = 520$ pooled nodes), all architectures were additionally evaluated across multiple random seeds to evaluate initialization stability:
- **Non-Graph MLP**: Pooled Accuracy = **$97.95\% \pm 0.22\%$** | Macro-F1 = **$0.9779 \pm 0.0031$**.
- **Heterogeneous GATv2**: Pooled Accuracy = **$84.17\% \pm 2.40\%$** | Macro-F1 = **$0.7501 \pm 0.0565$**.
- **Randomized-Edge GATv2**: Pooled Accuracy = **$77.82\% \pm 3.68\%$** | Macro-F1 = **$0.6915 \pm 0.0452$**.

#### Clarification on Confidence Intervals and Resampling Units
The 95% bootstrap confidence intervals ($B = 1000$ iterations) are computed by resampling **individual file predictions pooled across the 520 evaluated nodes**.
- **Descriptive within-sample uncertainty**: These intervals describe the sampling variability of the aggregate 520-file test sample under the fixed LOPO evaluation protocol.
- **Not project-level generalization uncertainty**: These intervals do **not** represent cluster-robust project-level generalization uncertainty. Software repositories represent natural clusters of widely disparate sizes (1 to 178 files) with overlapping LOPO training sets.
- **Limitations of Inference with $K=8$ Projects**: A project-level cluster bootstrap with only 8 independent repositories is statistically unviable and volatile (e.g., $34.4\%$ of cluster bootstrap resamples would omit the largest repository `python_cryptography` entirely). True project-to-project variability is properly quantified by the unweighted fold-level standard deviations reported above.

---

### 4.2 Aggregate Confusion Matrices ($N = 520$ Files, Seed 42 Converged)

#### Heterogeneous GATv2 (Genuine 14-dim, Seed 42):
$$\begin{pmatrix} 
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{True LOW (0)} & \mathbf{247} & 28 & 1 \\
\text{True MED (1)} & 15 & \mathbf{126} & 0 \\
\text{True HIGH (2)} & 1 & 74 & \mathbf{28}
\end{pmatrix}$$
- **Class 0 (LOW, $N=276$)**: Precision = $93.9\%$, Recall = **$89.5\%$**, F1 = **$0.916$**
- **Class 1 (MED, $N=141$)**: Precision = $55.3\%$, Recall = **$89.4\%$**, F1 = **$0.683$**
- **Class 2 (HIGH, $N=103$)**: Precision = **$96.6\%$**, Recall = **$27.2\%$**, F1 = **$0.424$**

#### Non-Graph Feature-Only MLP (14-dim, Seed 42):
$$\begin{pmatrix} 
& \text{Pred LOW} & \text{Pred MED} & \text{Pred HIGH} \\
\text{True LOW (0)} & \mathbf{275} & 1 & 0 \\
\text{True MED (1)} & 8 & \mathbf{132} & 1 \\
\text{True HIGH (2)} & 0 & 1 & \mathbf{102}
\end{pmatrix}$$
- **Class 0 (LOW, $N=276$)**: Precision = $97.2\%$, Recall = **$99.6\%$**, F1 = **$0.984$**
- **Class 1 (MED, $N=141$)**: Precision = $98.5\%$, Recall = **$93.6\%$**, F1 = **$0.960$**
- **Class 2 (HIGH, $N=103$)**: Precision = **$99.0\%$**, Recall = **$99.0\%$**, F1 = **$0.990$**

---

### 4.3 Continuous Score Rank Correlations
We evaluate rank monotonicity across all $N = 520$ file nodes using both Spearman's rank correlation ($\rho$) and Kendall's rank correlation ($\tau$):

1. **Continuous Heuristic Composite Score vs. Discrete Risk Tiers (0, 1, 2)**:
   - **Spearman $\rho$**: **$0.9090$** ($p = 5.05 \times 10^{-199}$)
   - **Kendall $\tau$**: **$0.7950$** ($p = 1.19 \times 10^{-115}$)
   - *Interpretation*: Confirms that the discrete tier thresholds preserve strong monotonic ordering over the continuous 7-factor composite score across the entire benchmark dataset.

2. **Out-of-Fold Continuous GATv2 Predictions vs. Continuous Heuristic Score**:
   - **Spearman $\rho$**: **$0.8985$** ($p = 2.66 \times 10^{-187}$)
   - **Kendall $\tau$**: **$0.7369$** ($p = 1.78 \times 10^{-129}$)

3. **Out-of-Fold Continuous MLP Predictions vs. Continuous Heuristic Score**:
   - **Spearman $\rho$**: **$0.9497$** ($p = 2.52 \times 10^{-263}$)
   - **Kendall $\tau$**: **$0.8476$** ($p = 1.26 \times 10^{-170}$)

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

### 4.5 Paired Permutation Tests across Model Architectures ($N = 520$, $B = 1000$)
To evaluate whether observed accuracy differences between architectures on the pooled out-of-fold sample ($N = 520$) are statistically significant, paired permutation tests were executed under the exchangeability null hypothesis $H_0: \mathbb{E}[\text{Acc}_A - \text{Acc}_B] = 0$:

| Model Comparison | $|\Delta \text{Acc}|$ | Permutation $p$-value | Statistical Interpretation |
| :--- | :---: | :---: | :--- |
| **GATv2 vs. Non-Graph MLP** | **15.00%** | **$p = 0.0010$** ($p < 0.001$) | Statistically significant difference; Non-Graph MLP outperforms GATv2 on pooled distillation accuracy. |
| **GATv2 vs. Edge-Shuffled Control** | **8.27%** | **$p = 0.0010$** ($p < 0.001$) | Statistically significant difference; genuine graph topology significantly outperforms randomized edge noise. |
| **GATv2 vs. Static Rule Baseline** | **30.96%** | **$p = 0.0010$** ($p < 0.001$) | Statistically significant difference; GATv2 significantly outperforms independent keyword AST matching. |
| **Non-Graph MLP vs. Static Rule Baseline** | **45.96%** | **$p = 0.0010$** ($p < 0.001$) | Statistically significant difference; MLP feature distillation significantly outperforms the rule baseline. |
| **GATv2 vs. Target Leakage (15-dim)** | **1.15%** | **$p = 0.0230$** | Marginal statistical delta; discrete classification does not critically rely on continuous scalar leakage. |

---

## 5. Controlled Target Leakage Ablation

| Configuration | Input Dim | Evaluation Mode | Pooled Accuracy | Unweighted Fold Mean Acc | Balanced Acc | Macro-F1 | Finding |
|---|---|---|---|---|---|---|---|
| **WITHOUT_BASE_RISK (Genuine)** | 14 | Cross-Repo LOPO | **83.08%** | **89.38%** | **73.12%** | **0.7176** | Evaluated without continuous target leakage (14-dim) |
| **WITH_BASE_RISK (Target Leaked)** | 15 | Cross-Repo LOPO | **81.92%** | **88.78%** | **72.91%** | **0.7167** | Evaluated with scalar `base_risk` appended to node feature vector |

---

## 6. Critical Scientific Analysis & Methodological Disclosures

### 6.1 Aggregation Sensitivity: Inability to Support a Model Ranking under LOPO
Under Leave-One-Project-Out evaluation across heterogeneous codebases (Go, Java, Python), model rankings completely invert depending on the aggregation method:
- **Pooled Sample Accuracy ($N=520$)**: $\text{Non-Graph MLP } (98.08\%) > \text{GATv2 } (83.08\%) > \text{Edge-Shuffled } (74.81\%)$.
- **Unweighted Fold Mean ($K=8$)**: $\text{GATv2 } (89.38\%) > \text{Non-Graph MLP } (84.35\%) > \text{Edge-Shuffled } (64.92\%)$.

#### Why the Ranking Inverts:
1. **Leverage of Micro-Repositories**: `python_bcrypt` has **$N = 1$ file**, commanding an entire $1/8\text{th}$ ($12.5\%$) of the unweighted fold mean. Because the MLP misclassifies that single file, its fold mean drops by $12.5\%$. Similarly, `python_itsdangerous` has **$N = 3$ files** ($12.5\%$ weight). Together, these 4 files ($0.77\%$ of the dataset) dictate **$25.0\%$ of the unweighted fold mean**.
2. **Dominance in Pooled Accuracy**: Conversely, `python_cryptography` ($N=178$) and `java_jjwt` ($N=170$) comprise 348 files ($66.9\%$ of data), dominating pooled accuracy while receiving only $25.0\%$ of the unweighted fold mean ($12.5\%$ each).
3. **High Fold Variance**: Fold standard deviations are high ($\pm 14.8\%$ for GATv2, $\pm 34.8\%$ for MLP, $\pm 30.3\%$ for Edge-Shuffled). With $K=8$ folds, the standard error of the mean ($\approx 12\%$) exceeds the differences between models.

**Academic Conclusion**: Under LOPO cross-validation across these 8 repositories of disparate sizes ($N \in [1, 178]$), high fold variance and small-repository leverage mean **no definitive model ranking between GATv2, MLP, and Edge-shuffling is statistically supportable**. Claims that local features definitively dominate or that GATv2 exhibits "topological sensitivity" are scientifically unsupportable overreaches.

### 6.2 Benchmark Corpus Structural Imbalance: Fold-7 Class Starvation & Fold-5 Majority Saturation
A detailed examination of class distributions across the 8 benchmark repositories explains the performance anomalies:

| Repository / Fold | Total Files | Class 0 (LOW) | Class 1 (MED) | Class 2 (HIGH) | % LOW | % HIGH |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`python_cryptography`** (Fold 7) | **178** | 2 | 77 | **99** | 1.1% | **55.6%** |
| **`java_jjwt`** (Fold 5) | **170** | **164** | 6 | **0** | **96.5%** | **0.0%** |
| `go_crypto` (Fold 1) | 111 | 75 | 34 | 2 | 67.6% | 1.8% |
| `go_jwt` (Fold 2) | 20 | 12 | 8 | 0 | 60.0% | 0.0% |
| `go_jwt_go` (Fold 3) | 19 | 6 | 12 | 1 | 31.6% | 5.3% |
| `java_java_jwt` (Fold 4) | 18 | 15 | 3 | 0 | 83.3% | 0.0% |
| `python_itsdangerous` (Fold 8) | 3 | 2 | 0 | 1 | 66.7% | 33.3% |
| `python_bcrypt` (Fold 6) | 1 | 0 | 1 | 0 | 0.0% | 0.0% |
| **Total Corpus** | **520** | **276 (53.1%)** | **141 (27.1%)** | **103 (19.8%)** | **53.1%** | **19.8%** |

1. **Fold 7 HIGH-Class Starvation**:
   - 99 of the 103 HIGH-risk files ($96.1\%$) reside in `python_cryptography`.
   - In LOPO Fold 7, the training set contains only 4 HIGH files out of 342 ($1.17\%$). GATv2's 27.18% HIGH recall under LOPO is entirely an artifact of Fold 7 starvation (predicting 26/99 in Fold 7).
   - In contrast, under **Stratified 5-Fold Cross-Validation** (where each fold's training set receives ~82 HIGH files), GATv2's HIGH recall rises to **74.76% (77/103)**.
2. **Fold 5 Majority-Class Ballast**:
   - `java_jjwt` accounts for 170 files ($32.7\%$ of corpus), of which 164 are LOW ($96.5\%$).
   - In LOPO Fold 5, every single model scores $\ge 97.65\%$ simply by predicting the dominant class. Fold 5 provides zero discriminative signal between models, but artificially anchors pooled accuracy.
3. **Corpus Concentration**:
   - Together, Fold 5 and Fold 7 account for **348 out of 520 files ($66.9\%$)**.

### 6.3 Architectural Safeguards and Product Behavior
Because weak-label distillation characterizes agreement with heuristic rules rather than real-world cryptanalysis, and because cross-repository validation is subject to severe dataset skew, AgileGraph enforces strict architectural safeguards:
1. **Deterministic Scanners as Authoritative Ground**: Deterministic static AST/regex scanners independently identify and catalog all cryptographic weaknesses. Known quantum-vulnerable primitives (e.g., RSA, DSA, ECC) are **never** suppressed or bypassed by the GNN.
2. **GNN as an Experimental Prototype Layer**: In production scans (`backend/src/pipeline/runner.py`), the system executes 100% deterministically using the AST scanners and the 7-factor heuristic engine. While weak-label distillation has been evaluated across the benchmark corpus, expert-label validation remains blocked; hence the PyTorch GATv2 model is isolated as an architectural prototype (`ml_status: ARCHITECTURAL_PROTOTYPE`).
3. **Graph Utility vs. GNN Classification**: The typed property graph remains foundational for interactive visualization, call-chain dependency tracing, blast-radius analysis, and migration planning, even though GATv2 message passing does not improve discrete classification over local feature vectors.

### 6.4 Independent AST Rule Baseline & Three-Tier PQC Taxonomy Verification
To ensure baseline independence and prevent data leakage from continuous heuristic labels:
1. **Decoupling from Heuristic Inputs**:
   - Earlier prototype baselines thresholded continuous features (`crypto_weakness` and `library_centrality`), which were derived directly from the heuristic engine.
   - The evaluated `Static Rule Baseline` directly inspects raw AST pattern matching findings from the code scanner (`crypto_usage` nodes) via word-bounded token analysis, completely independent of the 7-factor continuous inputs.
2. **Three-Tier PQC Migration Taxonomy**:
   - Cryptographic primitives are rigorously separated into three distinct migration tiers rather than conflated:
     - **Classically Broken**: MD5, SHA-1, DES, 3DES, RC4, Blowfish (classical cryptanalytic vulnerabilities; immediate remediation priority).
     - **Quantum-Vulnerable**: RSA, ECC, ECDSA, ECDH, DSA, Ed25519, X25519, DH (asymmetric schemes broken by Shor's polynomial-time algorithm on a CRQC; Mosca urgency / Harvest Now, Decrypt Later threats).
     - **Quantum-Resistant**: AES-128/192/256, ChaCha20, SHA-256/384/512, SHA-3, HMAC, and NIST standardized post-quantum schemes (ML-KEM, ML-DSA, SLH-DSA).
3. **Elimination of Substring False Positives**:
   - Substring matching on abbreviations like `"ec"` and `"des"` previously caused false positive hits on ordinary code identifiers (`"select"`, `"codec"`, `"description"`, `"destination"`).
   - The updated baseline enforces strict token-level regex word boundaries (`\b(ec|ecc)\b`, `\bdes\b`), completely eliminating non-crypto collisions.

### 6.5 Engineering & Statistical Invariant Refinements
1. **PyG Lazy Layer Materialization**:
   - `HeteroGATv2` utilizes lazy parameter initialization (`Linear(-1, hidden_channels)` and `GATv2Conv((-1, -1), ...)`). To ensure that the PyTorch Adam optimizer registers all model parameters and their momentum buffers, `create_hetero_gatv2` and all training pipelines execute a dummy forward pass (`initialize_lazy_layers`) prior to optimizer construction.
2. **Zero-Support Balanced Accuracy Correction**:
   - In cross-validation folds with skewed class representations (e.g., `java_jjwt` has 0 HIGH files, `python_bcrypt` has 0 LOW/HIGH files), naive balanced accuracy calculations divide by the total number of classes ($C=3$), penalizing missing classes as 0% recall and artificially deflating balanced accuracy.
   - The metric has been standardized to average recall strictly across classes with non-zero true support ($C_{\text{present}} = \{c \mid \text{support}(c) > 0\}$), in exact concordance with scikit-learn standard definitions (`sklearn.metrics.balanced_accuracy_score`).
3. **Safe PyG Artifact Deserialization (`weights_only=True`)**:
   - To eliminate arbitrary code execution risks associated with unpickling (`weights_only=False`), PyG graph storage schemas (`HeteroData`, `NodeStorage`, `EdgeStorage`, `BaseStorage`) are registered in `torch.serialization.add_safe_globals`, allowing all benchmark artifacts to be loaded safely under `weights_only=True`.

