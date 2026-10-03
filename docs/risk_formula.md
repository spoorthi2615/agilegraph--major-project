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

## 4. Data Sources
Metadata supplied by explicit project configurations, TLS scan artifacts, and parsed code manifests.

## 5. Unknown-Data Handling
If a value is not provided, the factor is strictly set to `None` with a confidence of `0.0`. It does NOT default to a fabricated value.

## 6. Initial library-centrality definition
(NOT FINALIZED)
Implemented as **In-Degree Centrality**: In-degree / (total_nodes - 1).

## 7. Initial migration-difficulty definition
(NOT FINALIZED)
Weighted inputs of: `code_change` (0.4), `dependency_change` (0.3), `certificate_change` (0.2), `infrastructure_change` (0.1).

## 8. What is NOT finalized yet
- Final heuristic weights have not yet been selected.
- Final centrality and migration mathematical definitions.
