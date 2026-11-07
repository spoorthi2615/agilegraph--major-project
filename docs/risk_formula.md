# Risk Formula

The heuristic risk score is an auditable formula combining several measurable components without relying on large-scale quantum computing assumptions.

## 1. Seven Heuristic Factors
- **data_sensitivity**: Sensitivity level of data protected by cryptography.
- **asset_criticality**: Criticality of the asset.
- **internet_exposure**: Degree of exposure to public networks.
- **crypto_weakness**: Current resistance of the algorithm.
- **cve_risk**: Presence of vulnerabilities via dependency enrichment.
- **library_centrality**: Centrality of the dependency.
- **migration_difficulty**: Estimated effort to replace the primitive.

## 2. Factor Definitions & 3. Normalization
Each factor is normalized to a value between `0.0` and `1.0`.
- **data_sensitivity**: LOW (0.25), MEDIUM (0.5), HIGH (0.75), CRITICAL (1.0).
- **asset_criticality**: LOW (0.25), MEDIUM (0.5), HIGH (0.75), CRITICAL (1.0).
- **internet_exposure**: INTERNAL (0.25), RESTRICTED (0.5), INTERNET_FACING (1.0).
- **crypto_weakness**: Quantum/Classical weak (e.g. MD5, RSA) -> 0.9-1.0. Quantum resistant -> 0.0.
- **cve_risk**: KNOWN_WITH_CVES (1.0), KNOWN_WITHOUT_CVES (0.0).

## 4. Mathematical Formula (Heuristic Engine)
The initial heuristic score uses a normalized weighted combination:
`base_risk = w1*S + w2*C + w3*E + w4*W + w5*V + w6*L + w7*M`
where `Σ wi = 1` and all factors are `[0,1]`.
*(Formula versioning: `heuristic-v0.1`)*

## 5. Weight Configuration
Weights are configurable and deterministic. They serve as transparent heuristic baseline priors for weak-supervision ranking and sensitivity analysis.

## 6. Missing-Data Policy
Uncertainty must not be hidden.
- **STRICT**: If any factor is missing (`None`), the calculation raises an error.
- **RENORMALIZE**: The available factors have their weights proportionally increased to sum to `1.0`. The result explicitly logs which factors were missing.

## 7. Score Interpretation & Audit
The output is an auditable `RiskScoreResult` decomposition including the score, missing policies, and a `weighted_contributions` dictionary explaining how much each factor contributed to the final result.

## 8. Baseline Interpretation
- The heuristic score is a deterministic rule-based baseline prior designed for operational triage and weak-supervision signal generation.
- Evaluation across the 8 pinned benchmark repositories establishes baseline monotonic ordering and sensitivity boundaries.

## 9. Mosca Migration Urgency Formulation

AgileGraph implements the Mosca Theorem to assess post-quantum migration urgency. It mathematically harmonizes the original Mosca inequality with a continuous readiness metric.

### 9.1 Original Mosca Inequality vs. Continuous Urgency Index
The classical Mosca theorem specifies a condition of cryptographic exposure:
$$X + Y > Z$$
where:
- **$X$ (Confidentiality Shelf-Life)**: Duration in months that encrypted data must remain confidential against future decryption (e.g., regulatory or intelligence lifespan).
- **$Y$ (Migration Timeline)**: Estimated duration in months to execute an organizational cryptographic migration to post-quantum standards.
- **$Z$ (Quantum Capability Horizon)**: Estimated timeline in months until a Cryptanalytically Relevant Quantum Computer (CRQC) emerges.

AgileGraph defines the normalized continuous **Mosca Urgency Index** $U$:
$$U = \frac{X + Y}{Z}$$

### 9.2 Relationship and Mathematical Equivalence
Both representations coexist and provide complementary operational value:
1. **The Inequality is the Boundary Decision Rule**:
   - $X + Y > Z \iff U > 1.0$: The required security lifetime and migration timeline strictly exceed the quantum threat horizon. Migration should have already begun; assets are immediately vulnerable to "Harvest Now, Decrypt Later" (HNDL) attacks. Categorized as `AT_RISK`.
   - $X + Y \le Z \iff U \le 1.0$: Migration timeline fits within the threat horizon. Categorized as `SAFE` (or `URGENT` when $0.8 \le U \le 1.0$ as an operational buffer).
2. **The Urgency Index Measures Continuous Proximity**:
   - While the boolean inequality only outputs a binary threshold, $U$ provides continuous prioritization across systems (e.g., $U=2.5$ represents far more severe deficit than $U=1.05$).
3. **Planning Horizon Disclaimer**:
   - Parameter $Z$ is strictly a configurable institutional planning parameter and risk threshold, not an empirical prediction of quantum physics or quantum hardware timelines.

## 10. Heuristic Engine Versioning: Production V1 vs. Optional Experimental V2

AgileGraph supports dual-engine heuristic execution with complete non-destructive coexistence and provenance tracking.

### 10.1 Production Default: Heuristic V1.0
- **Formula Version**: `heuristic-v1.0` (Default across all pipelines, API endpoints, and dashboards).
- **Mathematical Form**: Normalized weighted combination:
  $$\text{base\_risk} = \sum_{i=1}^{7} w_i \cdot f_i \quad \text{where } \sum w_i = 1$$
- **Classification Thresholds**:
  - $\text{LOW} < 0.30$
  - $\text{MEDIUM} \in [0.30, 0.60)$
  - $\text{HIGH} \ge 0.60$
- **Characteristics**: Preserves high specificity and high recall on non-cryptographic assets and test harnesses ($\text{Recall}_{\text{LOW}} = 89.66\%$), but underpredicts on cryptographic interfaces and key builders where direct cipher primitives are abstract ($\text{Recall}_{\text{MEDIUM}} = 3.92\%$, overall $\text{Macro-F1} = 0.3225$).

### 10.2 Optional Experimental Engine: Heuristic V2.0
- **Formula Version**: `heuristic-v2.0-experimental` (Accessible via explicit opt-in parameter `engine_version="v2"`).
- **Core Components**:
  1. **Data-Aware Threshold Calibration**: Decision thresholds fitted exclusively on training repositories via Leave-One-Repository-Out (LORO) cross-validation ($\theta_{\text{low}} = 0.18, \theta_{\text{high}} = 0.38$).
  2. **Semantic Graph Weakness Inheritance**: Propagates repository cryptographic weakness across verified `('file', 'IMPORTS', 'library')` edges targeting verified cryptographic libraries (`key`, `cipher`, `signature`, `mac`, `digest`, `secret`, `crypto`, `security`) to key abstractions with attenuation factor $\alpha = 0.55$.
- **Empirical LORO Out-of-Fold Performance**:
  - $\text{Macro-F1} = 0.7312$ (95% bootstrap CI: $[0.6432, 0.8084]$) vs. Baseline V1 $0.3225$ (Point) and $0.4960$ (LORO).
  - Weighted Cohen's $\kappa = 0.7028$ vs. Baseline V1 $0.2625$.
  - Overall Accuracy = $78.75\%$ ($126/160$) vs. Baseline V1 $33.12\%$ ($53/160$).
  - $\text{Recall}_{\text{HIGH}} = 91.25\%$ ($73/80$), $\text{Recall}_{\text{MEDIUM}} = 76.47\%$ ($39/51$).
- **Methodological Trade-Off (LOW Recall)**:
  - $\text{Recall}_{\text{LOW}}$ is $48.28\%$ ($14/29$) because test-harness files importing key builders receive attenuated inherited risk ($0.25 - 0.33$). V2 is conservative and migration-oriented, making it suitable for security teams seeking maximum discovery sensitivity.

## 11. Research Exploration: Candidate V3-Alpha (Experiment 3)

- **Status**: Purely an exploratory research ablation (`backend/scripts/run_heuristic_v2_evaluation.py` ablation study), **NOT implemented as a runtime engine**.
- **Mechanism**: Restricts graph weakness propagation strictly to asymmetric cryptographic primitives (RSA, DSA, ECDSA, ECDH) subject to polynomial-time Shor's algorithm compromise, while exempting symmetric ciphers (AES-256) and hash functions (SHA-384/512) which retain post-quantum security under quadratic Grover bounds.
- **Exploratory Metrics on 160-Asset Corpus**:
  - $\text{Macro-F1} = 0.8172$ (95% bootstrap CI: $[0.7484, 0.8806]$).
  - Linear Weighted $\kappa = 0.7782$.
  - Overall Accuracy = $83.75\%$ ($134/160$).
  - $\text{Recall}_{\text{LOW}} = 75.86\%$ ($22/29$), $\text{Recall}_{\text{MEDIUM}} = 76.47\%$ ($39/51$), $\text{Recall}_{\text{HIGH}} = 91.25\%$ ($73/80$).
- **Methodological Disclosure**:
  - Because keyword filter criteria were informed by inspecting misclassified assets from the 160-asset evaluation corpus, Experiment 3 is categorized as a **post-hoc exploratory asymmetric-specific propagation ablation**. Independent external validation on unseen codebases is required before production deployment.



