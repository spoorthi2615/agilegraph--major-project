# Ethics, Research Integrity & Scan Authorization

AgileGraph is an academic research project requiring rigorous methodology and responsible security practices. Optimization for "feature completion" must never supersede research correctness or ethical boundaries.

---

## 1. Scan Authorization & Ethical Boundaries
- **Active Scanning Scope**: Live network scanning of endpoints, certificates, and TLS handshakes is strictly limited to infrastructure controlled by the development team or for which explicit written authorization has been obtained.
- **Mandatory Authorization Flag**: The `--authorized` CLI flag is an enforced operational constraint for active scans. No unauthorized scanning workflows are permitted.
- **Passive Discovery**: Static code scanning and passive inspection of local source repositories or public Certificate Transparency logs do not probe third-party infrastructure.

---

## 2. Research Integrity Principles

### 2.1 Real vs. Synthetic Data
- Synthetic development fixtures must be explicitly documented and isolated (e.g., in `dataset/synthetic_dev_sandbox/`).
- Real-world scan results must never be simulated or fabricated. If real data is unavailable, it must be stated clearly.

### 2.2 Expert Annotations & Weak Supervision
- The heuristic risk score acts as weak supervision. It must not be presented as external human ground truth.
- If a panel of independent security experts has not been recruited, the system provides the data structures to support future expert evaluation without fabricating simulated raters or artificial agreement metrics.

### 2.3 CVE Evidence & Vulnerability Tracking
- "No CVE data retrieved" or an unconfigured CVE provider is NOT equivalent to "0 vulnerabilities". 
- Missing CVE data must be recorded as `UNAVAILABLE` or `UNKNOWN`.

### 2.4 Empirical Claims & Negative Results
- Benchmark scores and statistical significance must never be fabricated.
- If a model (such as GATv2) does not outperform a non-graph baseline (such as the MLP), the negative result must be reported honestly as an essential scientific finding.

### 2.5 Reproducibility & Determinism
- All experiments, feature extractions, and test suites must remain deterministic under fixed seeds.
- Dependency constraints and pinned benchmark repository commits ensure exact replication.
