# Architecture

## Layers
1. **Scanning and Data Collection**: Static analysis (Java, Python, Go) and TLS/certificate scanners.
2. **Risk-Graph Construction**: Heterogeneous graph stored in Neo4j/NetworkX.
3. **Graph Neural Network (GATv2)**: Weak supervision via heuristic risk score, leakage ablation.
4. **Presentation**: FastAPI backend and React/Tailwind frontend, Mosca Readiness Index module.

## Baselines
- Heuristic
- Rule-based
- CBOMkit
- GNN-refined
