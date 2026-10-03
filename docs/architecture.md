# Architecture

## Layers
1. **Scanning and Data Collection**: Static analysis (Python, Java, Go AST scanners) and authorization-gated TLS endpoint scanner (`INFRASTRUCTURE ONLY` — localhost/local development only; broad Internet TLS scanning not implemented).
2. **Risk-Graph Construction**: Heterogeneous graph stored in NetworkX (in-memory). Neo4j integration is configured in settings but is not installed or used in the current implementation.
3. **Graph Neural Network (GATv2)**: Architecture implemented; real training is `BLOCKED` pending expert labels. Weak supervision via heuristic risk score and leakage ablation infrastructure are implemented.
4. **Presentation**: FastAPI backend and React/Tailwind frontend, Mosca Readiness Index module.

## Baselines
- Heuristic
- Rule-based
- CBOMkit
- GNN-refined
