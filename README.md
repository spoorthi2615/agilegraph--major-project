# AgileGraph: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration

AgileGraph is an automated static analysis and graph-theoretic crypto-agility risk scoring system designed to help organizations inventory cryptographic assets, evaluate post-quantum vulnerability, calculate migration urgency via Mosca's theorem, and prioritize remediation workflows across multi-language enterprise codebases.

---

## 1. System Architecture

AgileGraph operates across four tightly-coupled architectural layers:

```
Source Repositories (Java, Python, Go)
   │
   ▼
[ 1. Discovery & Enriched Scanners ]
   ├─ Python (AST parsing of hashlib, cryptography, Crypto, ssl)
   ├─ Java (Regex & pattern matching for JCA/JCE primitives, jjwt)
   ├─ Go (AST & pattern matching for crypto/*, golang-jwt)
   ├─ Dependency Manifests (requirements.txt, pom.xml, go.mod) + OSV API Cache
   ├─ Inline Certificates & Private Keys (PEM block extraction & X.509 parsing)
   ├─ Endpoints (HTTP/HTTPS URL references)
   └─ Sensitive Data References (credentials, private keys, tokens)
   │
   ▼
[ 2. Typed Property Graph (NetworkX) ]
   ├─ 6 Node Types: File, CryptoUsage, Certificate, Endpoint, Library, SensitiveData
   └─ Valid Relationships: CONTAINS, IMPORTS, CALLS, USES_CERT, EXPOSES, PROTECTS, DEPENDS_ON
   │
   ▼
[ 3. Deterministic Risk & Triage Engine ]
   ├─ 7-Factor Heuristic Risk Score (Config-driven weights summing to 1.0)
   ├─ Missing Evidence Policy (RENORMALIZE or CONSERVATIVE)
   ├─ Mosca Readiness Index: U = (x + y) / z (AT_RISK, URGENT, SAFE)
   ├─ Migration Triage Matrix: f(base_risk, mosca_urgency, exposure_posture)
   └─ 6-State Lifecycle: DISCOVERED -> EVALUATED -> IN_PLANNING -> IN_MIGRATION -> VALIDATED -> DECOMMISSIONED
   │
   ▼
[ 4. Presentation & Analytics ]
   ├─ FastAPI REST Backend + SQLite Persistent Storage
   ├─ React / TypeScript / Tailwind CSS Interactive Dashboard
   └─ Comprehensive Audit Exporters (Markdown & JSON) with SHA-256 Provenance
```

---

## 2. Six-Node Ontology & Graph Semantics

The property graph schema strictly enforces 6 canonical node types and legal edge triplets per Section 5.3 of the Project Synopsis:

| Source Node | Edge Relationship | Target Node | Semantics |
| :--- | :--- | :--- | :--- |
| `File` | `CONTAINS` | `CryptoUsage` | Source file instantiates or invokes a cryptographic algorithm / API |
| `File` | `IMPORTS` | `Library` | Source file imports a dependency library |
| `File` | `CALLS` | `Endpoint` | Source file connects to or references a network endpoint |
| `File` | `USES_CERT` | `Certificate` | Source file bundles or references a certificate or private key |
| `File` | `PROTECTS` | `SensitiveData` | Cryptographic routine protects sensitive data or credentials |
| `Library` | `DEPENDS_ON` | `Library` | Upstream library depends on a transitive library dependency |

---

## 3. Seven-Factor Heuristic Risk Scoring

The composite risk score $s \in [0.0, 1.0]$ is computed deterministically using externalized weights defined in `backend/src/config/heuristic_weights.json`:

$$\text{Base Risk} = \sum_{i=1}^{7} w_i \cdot f_i, \quad \sum_{i=1}^{7} w_i = 1.0$$

| Factor ($f_i$) | Default Weight ($w_i$) | Rationale |
| :--- | :---: | :--- |
| **`crypto_weakness`** | 0.25 | Classical broken/asymmetric algorithms (RSA, ECC, DSA) are vulnerable to Shor's algorithm; small symmetric keys (AES-128) face Grover's speedup. |
| **`asset_criticality`** | 0.15 | Conservative 3-tier proxy: Explicit security modules (1.0), security-adjacent (0.75), shared utilities with in-degree $\ge 3$ (0.50), test fixtures (0.25). |
| **`data_sensitivity`** | 0.15 | Sensitivity classification of protected secrets; long-term credentials face Store Now, Decrypt Later (SNDL) attacks. |
| **`internet_exposure`** | 0.15 | Attack surface exposure; external-facing endpoints are directly exposed to quantum-capable adversaries. |
| **`migration_difficulty`** | 0.10 | Estimated refactoring complexity based on usage fan-out, hard-coded primitives, and API entanglement. |
| **`cve_risk`** | 0.10 | Known software vulnerabilities enriched via the public Open Source Vulnerabilities (OSV) database. |
| **`library_centrality`** | 0.10 | Degree centrality and transitive dependency blast radius within the software package dependency graph. |

### Missing-Evidence Policies
- **`RENORMALIZE`**: Weights of available factors are rescaled to sum to 1.0; missing factors do not penalize or artificially depress risk.
- **`CONSERVATIVE`**: Missing contextual evidence defaults to maximum uncertainty ($1.0$), reflecting worst-case security posture.

---

## 4. Mosca Readiness Index & Migration Triage

### Mosca's Theorem
- $x$ = Data shelf-life (years data must remain secure)
- $y$ = Migration time (years required to migrate to PQC)
- $z$ = Threat timeline (years until cryptanalytically relevant quantum computer)
- **Urgency Ratio**: $U = \frac{x + y}{z}$

| Urgency Band | Threshold | Action |
| :--- | :--- | :--- |
| **`AT_RISK`** | $U > 1.0$ | Data will be compromised before migration completes; immediate mitigation required. |
| **`URGENT`** | $0.8 \le U \le 1.0$ | Migration window is critically narrow; planning must commence immediately. |
| **`SAFE`** | $U < 0.8$ | Sufficient runway remains before quantum threat materialization. |

### Triage Matrix
Migration priority is assigned as an explicit function $f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$ producing actionable bands: **`CRITICAL`**, **`HIGH`**, **`MEDIUM`**, or **`LOW`**.

---

## 5. Migration Lifecycle & SQLite Persistence

Assets track post-quantum remediation across 6 immutable states managed by an append-only audit log:

$$\text{DISCOVERED} \longrightarrow \text{EVALUATED} \longrightarrow \text{IN\_PLANNING} \longrightarrow \text{IN\_MIGRATION} \longrightarrow \text{VALIDATED} \longrightarrow \text{DECOMMISSIONED}$$

- Stored in SQLite (`agilegraph.db`) with tables: `projects`, `migration_states`, and `migration_transitions`.
- Invalid state transitions (e.g., jumping from `DISCOVERED` directly to `VALIDATED`) are strictly rejected.

---

## 6. Research Scope & Evaluation Boundaries

Per the authoritative Project Synopsis, evaluation is conducted through:
1. **Functional Verification**: 100% pass rate across unit and integration test suites.
2. **Sensitivity Analysis**: Tornado sensitivity analysis verifying factor stability across $[0.5 \times w, 1.5 \times w]$.
3. **NIST Consistency Review**: Verification against FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA), and NIST IR 8547.
4. **Empirical Case Studies**: Multi-language evaluation across 8 pinned benchmark repositories.
5. **Architectural GATv2**: Graph Attention Network verified strictly for forward/backward gradient mechanics on synthetic dev data.

> **Operational Estimate Disclaimer**: All risk scores and migration priorities represent operational estimates based on deterministic heuristic rules. No claims of statistical predictive validity, empirical probability of quantum compromise, or expert consensus ground truth are made. Supervised ML evaluation on human panels is explicitly out of scope.

---

## 7. Quick Start & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

### Running Scans via CLI
```bash
cd backend

# 1. Run Headless Scan on Target Repository
python -m src.cli scan ../test_repo --output scan_results.json --project-id my-project

# 2. Generate Audit Report
python -m src.cli report scan_results.json --output audit_report.md
```

### Running Test Suites
```bash
# Backend Verification (Python)
cd backend
pytest

# Frontend Verification (Vitest & Vite Build)
cd frontend
npx vitest run
npm run build
```

---

## 8. License

This project is developed as an academic research project at NMAMIT. All code is licensed under the MIT License.
