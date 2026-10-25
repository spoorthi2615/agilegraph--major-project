# AgileGraph: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration

AgileGraph is an automated cryptographic discovery, property-graph construction, and crypto-agility risk scoring system designed for post-quantum cryptographic (PQC) migration. It inventories cryptographic assets across multi-language codebases, constructs typed property graphs, calculates deterministic heuristic risk scores enriched with contextual factor analysis, evaluates quantum migration urgency via Mosca's theorem, and provides an architectural Heterogeneous Graph Attention Network (GATv2) prototype for structural risk propagation.

---

## 1. System Architecture

AgileGraph processes repositories through four modular architectural layers:

```
Source Repositories (Python, Java, Go, Manifests)
   │
   ▼
[ 1. Discovery & Enriched Scanners ]
   ├─ Python AST Scanner (ast visitor for hashlib, cryptography, Crypto, ssl)
   ├─ Java Scanner (Regex & pattern matching for JCA/JCE primitives, jjwt)
   ├─ Go Scanner (Pattern matching for crypto/*, golang-jwt)
   ├─ Dependency Manifest Scanner (requirements.txt, pom.xml, go.mod) + OSV Cache
   ├─ Certificate & Key Scanner (PEM block extraction, X.509 parsing)
   ├─ Endpoint Scanner (URL references, TLS bindings)
   └─ Sensitive Data Scanner (credentials, private keys, secret tokens)
   │
   ▼
[ 2. Typed Property Graph (NetworkX) ]
   ├─ 6 Canonical Node Types: file, crypto_usage, certificate, endpoint, library, sensitive_data
   └─ 11 Authoritative Edge Triplets: CONTAINS, IMPORTS, DEPENDS_ON, CALLS, EXPOSES, PROTECTS, USES_CERT
   │
   ▼
[ 3. Deterministic Risk Engine & Prioritization ]
   ├─ 7-Factor Heuristic Risk Scoring (Configurable weights summing to 1.0)
   ├─ Missing Evidence Policy (RENORMALIZE or CONSERVATIVE)
   ├─ Mosca Readiness Index: U = (x + y) / z (AT_RISK, URGENT, SAFE)
   ├─ Migration Triage Matrix: Priority bands (CRITICAL, HIGH, MEDIUM, LOW)
   ├─ 6-State Remediation Lifecycle: DISCOVERED -> EVALUATED -> IN_PLANNING -> IN_MIGRATION -> VALIDATED -> DECOMMISSIONED
   └─ Architectural GATv2 Prototype (HeteroData PyG message-passing & explainability hooks)
   │
   ▼
[ 4. Presentation & Analytics ]
   ├─ FastAPI REST Backend + SQLite State Persistence
   ├─ React / TypeScript / Tailwind CSS Interactive Dashboard
   └─ Audit Exporters (Markdown & JSON) with SHA-256 Provenance Manifests
```

---

## 2. System Overview

AgileGraph bridges static application security testing (SAST) with post-quantum cryptanalysis planning. By transforming scattered cryptographic primitives into an interconnected graph, AgileGraph enables security engineers to understand not just *where* cryptography is used, but *what data it protects*, *which endpoints expose it*, and *how critical it is to system security*.

---

## 3. Graph Schema

The property graph schema strictly enforces 6 canonical node types and 11 legal edge triplets per Section 5.3 of the Project Synopsis:

### Canonical Node Types
- `file`: Source code file or configuration manifest.
- `crypto_usage`: Specific cryptographic algorithm invocation, cipher instantiation, or key exchange call.
- `certificate`: X.509 certificate, public key, or private key asset.
- `endpoint`: Network service URL or communication interface.
- `library`: Cryptographic software dependency or package.
- `sensitive_data`: High-value secret, credential, token, or sensitive payload.

### Authoritative Legal Edge Triplets

| Source Node | Edge Relationship | Target Node | Semantics |
| :--- | :--- | :--- | :--- |
| `file` | `CONTAINS` | `crypto_usage` | Source file declares or instantiates cryptographic usage |
| `file` | `CONTAINS` | `certificate` | Source file bundles or embeds a certificate or private key |
| `file` | `CONTAINS` | `sensitive_data` | Source file defines or references sensitive data / credentials |
| `file` | `IMPORTS` | `library` | Source file imports a software dependency |
| `file` | `DEPENDS_ON` | `library` | Source file or manifest declares a dependency on a library |
| `file` | `CALLS` | `endpoint` | Source file invokes or connects to a network endpoint |
| `endpoint` | `EXPOSES` | `crypto_usage` | Network endpoint exposes cryptographic functionality |
| `crypto_usage` | `PROTECTS` | `sensitive_data` | Cryptographic operation encrypts, hashes, or protects sensitive data |
| `crypto_usage` | `CALLS` | `library` | Cryptographic routine directly invokes an underlying library API |
| `crypto_usage` | `USES_CERT` | `certificate` | Cryptographic routine uses or binds a certificate/key |
| `endpoint` | `USES_CERT` | `certificate` | Network endpoint uses or binds a certificate for TLS/HTTPS |

---

## 4. Risk Scoring Methodology

AgileGraph computes a deterministic composite risk score $s \in [0.0, 1.0]$ based on 7 contextual security factors with externalized weights:

$$\text{Base Risk} = \sum_{i=1}^{7} w_i \cdot f_i, \quad \sum_{i=1}^{7} w_i = 1.0$$

| Factor ($f_i$) | Default Weight ($w_i$) | Rationale |
| :--- | :---: | :--- |
| **`crypto_weakness`** | 0.25 | Classical broken or asymmetric algorithms (RSA, ECC, DSA) are vulnerable to Shor's algorithm; small symmetric keys (AES-128) face Grover's speedup. |
| **`asset_criticality`** | 0.15 | Conservative 3-tier proxy: Explicit security modules (1.0), security-adjacent code (0.75), shared utilities with in-degree $\ge 3$ (0.50), test fixtures (0.25). |
| **`data_sensitivity`** | 0.15 | Sensitivity classification of protected secrets; long-term credentials face Store Now, Decrypt Later (SNDL) attacks. |
| **`internet_exposure`** | 0.15 | Attack surface exposure; external-facing endpoints are directly accessible to remote adversaries. |
| **`migration_difficulty`** | 0.10 | Estimated refactoring complexity based on usage fan-out, hard-coded primitives, and API entanglement. |
| **`cve_risk`** | 0.10 | Known software vulnerabilities enriched via the public Open Source Vulnerabilities (OSV) database. |
| **`library_centrality`** | 0.10 | Degree centrality and transitive dependency blast radius within the software package dependency graph. |

### Missing-Evidence Policies
- **`RENORMALIZE`** (Default): When factor evidence is missing (e.g. offline CVE lookup), weights of observed factors are rescaled to sum to 1.0 so unobserved factors do not artificially depress risk.
- **`STRICT` / `CONSERVATIVE`**: Missing evidence defaults to maximum uncertainty ($1.0$), reflecting a cautious worst-case security posture.

### Scoring Operational Distinction
- **Operational Engine**: Deterministic heuristic calculation ($s \in [0.0, 1.0]$) providing immediate, reproducible baseline assessments.
- **Prototype Engine**: Heterogeneous GATv2 model infrastructure exploring structural propagation over the typed property graph.

---

## 5. PQC Migration Prioritization

### Mosca's Theorem
Post-quantum migration urgency is quantified via Mosca's theorem:
- $x$ = Data shelf-life (years information must remain protected)
- $y$ = Migration duration (years required to transition infrastructure to PQC)
- $z$ = Threat timeline (years until a Cryptanalytically Relevant Quantum Computer emerges)

$$\text{Urgency Ratio } U = \frac{x + y}{z}$$

| Urgency Band | Threshold | Operational Action |
| :--- | :--- | :--- |
| **`AT_RISK`** | $U > 1.0$ | Immediate mitigation required; data will be compromised before migration completes. |
| **`URGENT`** | $0.8 \le U \le 1.0$ | Migration window is critically narrow; planning and algorithm replacement must begin. |
| **`SAFE`** | $U < 0.8$ | Sufficient runway remains before quantum threat materialization. |

### Triage Matrix
Composite migration priority combines base risk, Mosca urgency, and exposure posture into four actionable triage bands:
- **`CRITICAL`**: Quantum-vulnerable asymmetric primitives protecting high-shelf-life sensitive data on internet-exposed endpoints.
- **`HIGH`**: Quantum-vulnerable primitives with elevated structural centrality or active deprecation notices.
- **`MEDIUM`**: Symmetric algorithms with borderline key lengths (AES-128) or internal services.
- **`LOW`**: Quantum-resistant symmetric configurations (AES-256) or test code.

---

## 6. Scanners

AgileGraph includes multi-language static scanners:
- **Python Scanner**: Uses Python's native `ast` module to visit call expressions, imports, and cryptographic primitive instantiations across `hashlib`, `cryptography`, `Crypto`, and `ssl`.
- **Java Scanner**: Regex and pattern-based analysis detecting Java Cryptography Architecture (JCA/JCE) ciphers, key factories, and JWT libraries (`jjwt`, `java-jwt`).
- **Go Scanner**: Pattern-based AST matching targeting Go standard library packages (`crypto/tls`, `crypto/rsa`, `crypto/aes`, `crypto/elliptic`) and third-party JWT implementations.
- **Dependency Manifest Scanner**: Parses `requirements.txt`, `pom.xml`, and `go.mod` to construct software library nodes and resolve version vulnerabilities against the OSV cache.
- **Certificate & Secret Extractors**: Detects embedded PEM blocks, private keys, API secrets, and TLS endpoint bindings.

---

## 7. Corpus and Benchmarks

AgileGraph evaluates multi-language coverage across 8 pinned open-source repositories:

| Language | Repository | Size Tier | Description |
| :--- | :--- | :--- | :--- |
| Python | `python_cryptography` | Large | Core cryptographic recipe library |
| Python | `python_bcrypt` | Small | Password hashing utility |
| Python | `python_itsdangerous` | Small | Cryptographic data signing |
| Java | `java_jjwt` | Large | Java JWT library |
| Java | `java_java_jwt` | Medium | Auth0 Java JWT implementation |
| Go | `go_crypto` | Large | Go supplementary cryptographic libraries |
| Go | `go_jwt` | Small | Golang JWT implementation |
| Go | `go_jwt_go` | Small | Legacy dgrijalva JWT implementation |

### Corpus Management
- **Manifest**: Located at `backend/dataset/artifacts/manifest.json` (`corpus_v1`).
- **Build Pipeline**: Execute `python backend/scripts/build_corpus.py` to scan all 8 repositories, construct property graphs, compute deterministic heuristic scores, and serialize PyG `HeteroData` tensors.
- **Summary Utility**: Run `python backend/scripts/corpus_summary.py` to inspect descriptive distributions of scores and factor missingness.
- *Note*: Benchmark repository sources in `backend/dataset/corpus/` are gitignored to preserve clean version control; run `build_corpus.py` to generate artifacts locally.

---

## 8. GATv2 Architecture Prototype

AgileGraph implements a Heterogeneous Graph Attention Network (GATv2) using PyTorch Geometric (`torch_geometric`):
- **Heterogeneous Transformation**: Wraps a homogeneous GATv2 using PyG's `to_hetero` transformation, enabling typed message passing across all 6 node categories and 11 edge types.
- **Feature Extraction**: Extracts 7 normalized context factor features per node with deterministic missing-factor masking.
- **Leakage Ablation**: Includes a configurable `include_base_risk` flag (default `False`) to verify that the GNN learns structural relationships rather than memorizing heuristic weak-supervision labels.
- **Explainability**: Provides gradient-based feature attribution hooks (`compute_gradient_feature_importance`) for node and edge attribution.
- **Status**: The ML infrastructure, forward pass, backward pass, gradient flow, and explainability hooks are fully verified on synthetic test graphs. Real empirical training and benchmark evaluations are future research work pending an empirical training corpus.

---

## 9. CLI Usage

AgileGraph includes a command-line interface for automated scanning and report generation.

### Installation
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Basic Scan
```bash
# Scan a local repository
python -m src.cli scan ./sample_repo --output scan_results.json --project-id my-project
```

### CLI Options
- `repository`: Path to local directory to scan.
- `--output`: Filepath to write structured output (default: stdout).
- `--project-id`: Identifier for the project (default: derived from repository directory name).
- `--format`: Output format: `json` or `markdown` (default: `json`).
- `--missing-data-policy`: Missing factor strategy: `RENORMALIZE` or `CONSERVATIVE` (default: `RENORMALIZE`).

### Generating Audit Reports
```bash
python -m src.cli report scan_results.json --output audit_report.md
```

---

## 10. API Reference

AgileGraph provides a REST API via FastAPI:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/scan` | `POST` | Scan a repository path and return graph and risk summary |
| `/api/graph/{project_id}` | `GET` | Retrieve the typed property graph (nodes and edges) |
| `/api/risk/{project_id}` | `GET` | Retrieve scored assets, factor breakdowns, and weights |
| `/api/pqc/priority/{project_id}` | `GET` | Calculate Mosca migration urgency and triage priority |
| `/api/reports/export/{project_id}` | `GET` | Export audit report in Markdown or JSON format |
| `/api/product/pqc-readiness/{project_id}` | `GET` | Retrieve high-level PQC readiness coverage indicators |

### Example Scan Request
```bash
curl -X POST "http://localhost:8000/api/scan" \
  -H "Content-Type: application/json" \
  -d '{"repository_path": "./sample_repo", "project_id": "demo-proj", "missing_data_policy": "RENORMALIZE"}'
```

---

## 11. Web Dashboard

The web interface is built with React 19, TypeScript, Vite, and TailwindCSS:
- **Dashboard**: High-level posture overview, risk distribution chart, and key metrics.
- **Cryptographic Inventory**: Filterable table of discovered algorithms, keys, certificates, and endpoints.
- **Graph Visualization**: Interactive 2D force-directed graph rendering typed nodes and edge connections.
- **PQC Readiness**: Mosca urgency timeline and migration candidate breakdown.
- **Reports**: Configurable audit export in Markdown, JSON, and CSV formats.

### Setup and Running
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 12. Project Structure

```
agilegraph/
├── backend/
│   ├── dataset/
│   │   ├── artifacts/             # Pinned corpus artifacts (manifest.json, report.json)
│   │   └── cache/                 # Local OSV / CVE SQLite caches
│   ├── scripts/
│   │   ├── build_corpus.py        # Benchmark corpus build pipeline
│   │   ├── corpus_summary.py      # Corpus descriptive summary utility
│   │   └── generate_case_studies.py # Illustrative case study generator
│   ├── src/
│   │   ├── api/                   # FastAPI routes and Pydantic schemas
│   │   ├── config/                # Heuristic weights and factor configurations
│   │   ├── dataset/               # Dataset models and storage managers
│   │   ├── graph/                 # Property graph schema, builder, and validator
│   │   ├── ml/                    # GATv2 model, HeteroData converter, features
│   │   ├── pipeline/              # Orchestrator, reporter, and report templates
│   │   ├── risk/                  # Heuristic risk engine, factor extractors, Mosca
│   │   ├── scanners/              # Python AST, Java, Go, and manifest scanners
│   │   ├── storage/               # SQLite database models and migrations
│   │   ├── cli.py                 # Command-line interface
│   │   └── main.py                # FastAPI application entrypoint
│   └── tests/                     # Pytest suite (unit, integration, e2e, ml)
├── docs/                          # Architecture, review, and methodology documentation
├── frontend/                      # React / TypeScript / Vite web dashboard
│   ├── src/
│   │   ├── api/                   # API client and TypeScript interfaces
│   │   ├── components/            # UI views (Dashboard, Graph, Inventory, Reports)
│   │   └── tests/                 # Vitest component and integration tests
├── .github/workflows/ci.yml       # GitHub Actions CI pipeline
├── .gitignore
├── LICENSE
└── README.md
```

---

## 13. Research Integrity and Disclaimers

### Operational Functionality
- Automated static scanning across Python, Java, Go, and package manifests is operational.
- Typed property graph construction with strict 6-node and 11-edge schema enforcement is operational.
- Deterministic heuristic risk scoring with 7 context factors and configurable weights is operational.
- Mosca's theorem migration prioritization and 6-state lifecycle tracking are operational.
- CLI, REST API, React dashboard, and case-study generation are operational.

- **GATv2 Model & Cross-Validation**: The Heterogeneous GATv2 model was trained and evaluated via 8-fold Leave-One-Project-Out (LOPO) cross-validation on the 8-repository benchmark (520 files), achieving 66.73% accuracy (Macro-F1: 0.5560) vs. Majority (22.69%) and Corrected Static Rule (42.12%) baselines. The GNN functions as a weak-supervision risk-prioritization layer, while deterministic static scanning independently guarantees all detected cryptographic weaknesses are surfaced.
- **Operational Heuristic Prior**: All risk scores represent deterministic heuristic assessments based on initial configurable factor weights. They are not empirical probabilities of compromise or certified security guarantees.
- **No Fabricated Data**: This repository contains no simulated expert panels, fake Cohen's Kappa agreements, or fabricated empirical benchmark scores.

---

## 14. License and Citation

### License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

### Citation
If you use AgileGraph in academic research, please cite:

```bibtex
@misc{agilegraph2026,
  author = {AgileGraph Team},
  title = {AgileGraph: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration},
  year = {2026},
  howpublished = {\url{https://github.com/spoorthi2615/agilegraph--major-project}},
  note = {Final-Year B.Tech Cyber Security Project, NMAMIT}
}
```
