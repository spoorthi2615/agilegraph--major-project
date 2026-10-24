# AgileGraph Architectural Decision Records (ADRs)

This document records key architectural, scope, and mathematical decisions made to align the AgileGraph codebase with the authoritative Project Synopsis.

---

## ADR-001: Separation of Objective Risk Scoring from Downstream Migration Planning

- **Context**: Prior iterations conflated planning urgency (Mosca theorem) with cryptographic risk scoring, risking circular feedback or subjective distortion of graph-learned risk metrics.
- **Decision**: 
  - The 7-factor heuristic risk score $R \in [0, 1]$ is strictly an objective, static property graph metric derived from code artifacts, dependencies, and network exposure.
  - Migration priority is modeled as a downstream planning triage function $f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$.
  - Mosca inputs ($x, y, z$) are planning assumptions and do not alter the base risk score $R$.
- **Status**: Implemented in `backend/src/risk/migration_priority.py` and specified in `docs/TRIAGE_SPEC.md`.

---

## ADR-002: Mosca Readiness Index Formula and Urgency Bands

- **Context**: The classical Mosca theorem states that if $x + y > z$, data is at risk. A binary condition lacks gradation for assets approaching the quantum horizon.
- **Decision**:
  - Implement readiness index $U = \frac{x + y}{z}$.
  - Define three explicit urgency bands:
    - $U > 1.0 \implies \text{AT\_RISK}$
    - $0.8 \le U \le 1.0 \implies \text{URGENT}$ (20% safety margin buffer)
    - $U < 0.8 \implies \text{SAFE}$
  - Invalid inputs ($z \le 0$, negative durations, missing inputs) strictly yield $\text{INSUFFICIENT\_DATA}$.
  - Disclaimer mandatory: $z$ is an organizational planning assumption, not a physical quantum computing breakthrough forecast.
- **Status**: Implemented in `backend/src/risk/mosca.py` and tested in `backend/tests/risk/test_mosca.py`.

---

## ADR-003: Heuristic 7-Factor Weights and Missing-Evidence Policies

- **Context**: Heuristic risk factors may not all be observable for every code asset (e.g., non-library nodes lack dependency vulnerabilities; files without network bindings lack endpoint exposure).
- **Decision**:
  - Externalize all weights in `backend/src/config/heuristic_weights.json` with documented rationale, strictly summing to 1.0.
  - Implement two deterministic missing-evidence policies:
    1. `RENORMALIZE` (default operational): Sum weights of observed factors and re-weight proportionally to sum to 1.0.
    2. `CONSERVATIVE`: Treat unobserved evidence as unmitigated risk ($1.0$), ensuring risk is never underestimated.
  - Resulting score is clamped strictly to $[0.0, 1.0]$.
- **Status**: Implemented in `backend/src/risk/heuristic.py` and `backend/src/risk/weights.py`.

---

## ADR-004: Typed Property Graph Schema Alignment (Synopsis Section 5.3)

- **Context**: The codebase previously allowed non-canonical relationships (e.g. `(File, EXPOSES, Endpoint)`) and arbitrary edge types.
- **Decision**:
  - Exactly 6 node types: `File`, `CryptoUsage`, `Certificate`, `Endpoint`, `Library`, `SensitiveData`.
  - Canonical edge types enforced:
    - `(File, CONTAINS, CryptoUsage | Certificate | SensitiveData)`
    - `(File, CALLS, Endpoint)`
    - `(File, IMPORTS, Library)`
    - `(File, DEPENDS_ON, Library)`
    - `(Endpoint, EXPOSES, CryptoUsage)`
    - `(CryptoUsage, PROTECTS, SensitiveData)`
    - `(CryptoUsage, USES_CERT, Certificate)`
    - `(Endpoint, USES_CERT, Certificate)`
    - `(CryptoUsage, CALLS, Library)`
  - Enforce graph integrity validation (`validate_graph` and `AgileGraph.validate_integrity()`) refusing dangling edges or illegal triplets.
- **Status**: Implemented in `backend/src/graph/schema.py`, `backend/src/graph/validation.py`, and `backend/src/graph/builder.py`.

---

## ADR-005: 3-Tier Conservative Criticality Proxy

- **Context**: Heuristic factor `criticality` previously used broad keyword matching (`crypto`, `jwt`, `token`) that tagged ~80% of files in cryptographic repositories as critical ($0.75$), masking architectural centrality.
- **Decision**:
  - Restructure into 3 conservative tiers:
    - $1.0$: Explicit security entry points / authentication core.
    - $0.75$: Demonstrably security-critical implementation modules (tight path matching).
    - $0.50$: Shared architectural utilities with in-degree $\ge 3$.
    - $0.25$: Test, example, and mock fixtures.
    - `None`: Neutral/uncertain context handled via missing-evidence policy.
- **Status**: Implemented in `backend/src/risk/criticality.py` and tested in `backend/tests/risk/test_criticality.py`.

---

## ADR-006: Out-of-Scope Classification and Archival of Expert Annotations

- **Context**: The project synopsis explicitly defines AgileGraph's validation through functional verification, sensitivity analysis, NIST consistency review, and case studies across 8 pinned repositories. Supervised training on human expert panels and claims of "predictive accuracy" or "F1 agreement" are explicitly out of scope.
- **Decision**:
  - Preserve all historical expert annotation code and datasets in dedicated branch `archive/expert-annotation` and folder `docs/archive/`.
  - Remove references to legacy expert-label placeholders or human-expert ground truth from production pipelines.
  - Frame GATv2 strictly as an architectural prototype verified for mechanical forward/backward gradient correctness on synthetic dev data, without claims of predictive superiority over the heuristic baseline.
- **Status**: Branch created; active alignment in Phase 5.
