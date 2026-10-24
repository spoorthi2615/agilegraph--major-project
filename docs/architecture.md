# Architecture

## Layers
1. **Static Discovery and Enrichment**: Static source analysis (Python AST, Java regex with variable tracking, Go regex patterns), certificate/key scanners, network endpoint bindings, sensitive data detectors, and dependency manifests with public OSV CVE enrichment.
2. **Typed Property Graph**: In-memory heterogeneous graph stored in NetworkX conforming strictly to the 6-node typed schema (`File`, `CryptoUsage`, `Certificate`, `Endpoint`, `Library`, `SensitiveData`), with schema-legal directed triplets and SQLite persistence for migration lifecycle state machine and transition audit logging.
3. **Deterministic Heuristic Risk Model**: Documented 7-factor weighted scoring model ($R \in [0.0, 1.0]$) configured in `backend/src/config/heuristic_weights.json` with deterministic missing-evidence handling policies (`RENORMALIZE` and `CONSERVATIVE`).
4. **Migration Triage & Mosca Readiness**: Downstream operational queue planning as $f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$ with readiness index $U = (x+y)/z$ and urgency bands (`AT_RISK`, `URGENT`, `SAFE`).
5. **Presentation & API**: FastAPI REST backend and React/TypeScript web dashboard for crypto-inventory exploration, factor explainability, and lifecycle progression.
6. **Machine Learning Prototype**: HeteroGATv2 architectural implementation verified mechanically for forward/backward gradient correctness strictly on synthetic development data.
