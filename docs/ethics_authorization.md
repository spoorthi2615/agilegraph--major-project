# Ethics, Research Integrity & Scan Authorization

AgileGraph is an academic research project requiring rigorous methodology and responsible security practices. Optimization for "feature completion" must never supersede research correctness or ethical boundaries.

---

## 1. Scan Authorization & Ethical Boundaries
- **Active Scanning Scope**: Live network scanning of endpoints, certificates, and TLS handshakes is strictly limited to infrastructure controlled by the development team or for which explicit written authorization has been obtained.
- **Mandatory Authorization Flag**: The `--authorized` CLI flag is an enforced operational constraint for active scans. No unauthorized scanning workflows are permitted.
- **Passive Discovery**: Static code scanning and passive inspection of local source repositories or public Certificate Transparency logs do not probe third-party infrastructure.

---

## 2. Research Integrity Principles

### 2.1 Empirical Ground Truth & Static Analysis
- Real-world scan results must never be simulated or fabricated. All property graphs and risk factors reflect deterministic AST and dependency extraction.

### 2.2 Ground Truth & Weak Supervision
- The heuristic risk score acts as weak supervision. It must not be presented as external human ground truth.
- In the absence of external benchmark ground truth labels, all evaluations measure approximation fidelity to rule-based priors.

### 2.3 CVE Evidence & Vulnerability Tracking
- "No CVE data retrieved" or an unconfigured CVE provider is NOT equivalent to "0 vulnerabilities". 
- Missing CVE data must be recorded as `UNAVAILABLE` or `UNKNOWN`.

### 2.4 Empirical Claims & Negative Results
- Benchmark scores and statistical significance must never be fabricated.
- If a model (such as GATv2) does not outperform a non-graph baseline (such as the MLP), the negative result must be reported honestly as an essential scientific finding.

### 2.5 Reproducibility & Determinism
- All experiments, feature extractions, and test suites must remain deterministic under fixed seeds.
- Dependency constraints and pinned benchmark repository commits ensure exact replication.
