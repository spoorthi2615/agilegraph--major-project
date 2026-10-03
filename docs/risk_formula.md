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
Weights are currently configurable. **They are NOT EXPERT-VALIDATED final project weights.** They are initial values meant for weak supervision and later sensitivity/AHP-lite testing.

## 6. Missing-Data Policy
Uncertainty must not be hidden.
- **STRICT**: If any factor is missing (`None`), the calculation raises an error.
- **RENORMALIZE**: The available factors have their weights proportionally increased to sum to `1.0`. The result explicitly logs which factors were missing.

## 7. Score Interpretation & Audit
The output is an auditable `RiskScoreResult` decomposition including the score, missing policies, and a `weighted_contributions` dictionary explaining how much each factor contributed to the final result.

## 8. What is NOT finalized yet
- Final heuristic weights have not yet been selected.
- Final centrality and migration mathematical definitions.
- The initial heuristic score is a weak-supervision signal and not ground-truth expert labeling.
- Synthetic ranking fixtures exist for testing only and do not represent real security assessments.
