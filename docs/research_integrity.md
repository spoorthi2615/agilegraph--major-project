# Research Integrity

AgileGraph is an academic research project requiring rigorous methodology. Optimization for "feature completion" must never supersede research correctness. 

## Explicit Rules for Integrity

### Real vs. Synthetic Data
- Synthetic fixtures must be explicitly documented and isolated (e.g., in `tests/fixtures/`).
- Real-world scan results must not be simulated or invented. If real data is unavailable, state it clearly.

### Expert Labels
- If the required panel of four security experts has not been recruited or their labels collected, the system may provide the *pipeline* to process these labels, but it MUST NOT generate fake experts or fabricate metrics like Cohen's Kappa.

### CVE Evidence
- "No CVE data retrieved" or an unconfigured CVE provider is NOT equivalent to "0 vulnerabilities". 
- Missing CVE data must be recorded as `UNAVAILABLE` or `UNKNOWN`.

### Benchmark and Statistical Results
- Do not fabricate benchmark scores or statistical significance merely to demonstrate that the model works. 
- If the GATv2 model does not demonstrate improvement over the heuristic baseline, report the negative result honestly. Comparisons must be actually calculated.

### Model Results & Weak Supervision
- The heuristic risk score acts as weak supervision. Do not accidentally treat the heuristic label as the ultimate ground truth.
- Train/test leakage must be prevented. The leakage-ablation experiment is a strict requirement to verify that the GNN is learning structural context rather than just copying the heuristic label.

### Scan Authorization
- Active TLS/Endpoint scanning is strictly limited to infrastructure controlled by the team or for which explicit written permission exists.
- The `--authorized` flag is a mandatory constraint for active scans. No unauthorized scanning workflows are permitted.

### Reproducibility
- The environment and testing suite must remain deterministic. 
- All dependencies must preserve version constraints to ensure exact replication.

### Limitations
- Known limitations of the initial prototype (such as regex-based AST parsing or unweighted centrality formulas) must be clearly documented. Do not claim comprehensive capabilities that do not exist.
