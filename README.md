# AgileGraph: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration

[![Backend Tests](https://img.shields.io/badge/Backend%20Tests-413%20Passed%20(4%20skipped)-success?style=flat-square&logo=pytest)](docs/evaluation.md)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-38%20Passed-success?style=flat-square&logo=vitest)](frontend/)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square&logo=python)](backend/)
[![React Version](https://img.shields.io/badge/Frontend-React%2019%20%7C%20TypeScript%20%7C%20Vite-61dafb?style=flat-square&logo=react)](frontend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Academic Project](https://img.shields.io/badge/B.Tech%20Cyber%20Security-Major%20Project%20(2023--2027)-darkblue?style=flat-square)](docs/AGILEGRAPH_PROJECT_SYNOPSIS.pdf)

> **Major Project (B.Tech Cyber Security, 2023–2027)**  
> **Department of Computer Science (Cyber Security)**  
> **NMAM Institute of Technology (NMAMIT), Nitte (Deemed to be University), Karnataka**  
>
> **Project Team:**  
> • **Spoorthi** (`NNM23CB058`)  
> • **Sindhoora R** (`NNM23CB057`)  
> • **Nivedita V Shetty** (`NNM23CB033`)  
> • **Sujan S** (`NNM23CB062`)  
>
> **Project Guide:**  
> • **Ms. Madhushree**, Assistant Professor, Dept. of CSE (Cyber Security), NMAMIT  
>
> **Official Project Proposal & Synopsis Downloads:**  
> • 📄 [**Download Project Synopsis (PDF)**](docs/AGILEGRAPH_PROJECT_SYNOPSIS.pdf)  
> • 📝 [**Download Project Synopsis (Word DOCX)**](docs/AGILEGRAPH_PROJECT_SYNOPSIS.docx)

AgileGraph is an automated cryptographic discovery, typed property-graph modeling, and crypto-agility risk scoring system engineered for post-quantum cryptographic (PQC) migration. It inventories cryptographic primitives across multi-language codebases (Python, Java, Go, and package manifests), constructs formal 6-node property graphs, computes deterministic 7-factor heuristic risk scores enriched with contextual factor analysis, evaluates quantum migration urgency via Mosca's theorem, tracks migration across a 6-state remediation lifecycle, and provides an architectural Heterogeneous Graph Attention Network (GATv2) model for structural risk propagation.

The platform includes a modern public landing page, defensive user authentication (bcrypt + PyJWT with server-side revocation), strict multi-user project data isolation, and comprehensive audit-ready export tools.

---

## Table of Contents

- [Academic Project & Team Details](#academic-project--team-details)
- [1. System Architecture](#1-system-architecture)
- [2. Key Capabilities](#2-key-capabilities)
- [3. Graph Schema & Edge Semantics](#3-graph-schema--edge-semantics)
- [4. Risk Scoring Methodology](#4-risk-scoring-methodology)
- [5. Post-Quantum Prioritization & Lifecycle](#5-post-quantum-prioritization--lifecycle)
- [6. Multi-Language Scanners](#6-multi-language-scanners)
- [7. Benchmark Corpus & Reproducibility](#7-benchmark-corpus--reproducibility)
- [8. GATv2 Graph Neural Network & Evaluation](#8-gatv2-graph-neural-network--evaluation)
- [9. Authentication & Multi-User Data Isolation](#9-authentication--multi-user-data-isolation)
- [10. Public Landing Page & Web Dashboard](#10-public-landing-page--web-dashboard)
- [11. CLI Usage](#11-cli-usage)
- [12. REST API Reference](#12-rest-api-reference)
- [13. Installation & Getting Started](#13-installation--getting-started)
- [14. Project Directory Structure](#14-project-directory-structure)
- [15. Verification & Test Suite Status](#15-verification--test-suite-status)
- [16. Research Integrity & Disclaimers](#16-research-integrity--disclaimers)
- [17. License & Citation](#17-license--citation)

---

## Academic Project & Team Details

| Item | Details |
| :--- | :--- |
| **Project Title** | **AGILEGRAPH: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration** |
| **Subtitle / Focus** | *Heterogeneous GNN Risk Propagation and Explainable Migration Prioritization* |
| **Program** | Bachelor of Technology (B.Tech) in Computer Science (Cyber Security) |
| **Academic Year** | 2023 – 2027 (Final Year Major Project) |
| **Institution** | NMAM Institute of Technology (NMAMIT), Nitte (Deemed to be University), Karnataka |
| **Project Guide** | **Ms. Madhushree**, Assistant Professor, Department of Computer Science (Cyber Security) |
| **Student Investigators** | **1. Spoorthi** (`NNM23CB058`)<br>**2. Sindhoora R** (`NNM23CB057`)<br>**3. Nivedita V Shetty** (`NNM23CB033`)<br>**4. Sujan S** (`NNM23CB062`) |
| **Formal Synopsis** | [PDF Document](docs/AGILEGRAPH_PROJECT_SYNOPSIS.pdf) \| [Word Document (.docx)](docs/AGILEGRAPH_PROJECT_SYNOPSIS.docx) |

---

## 1. System Architecture

AgileGraph processes repositories through five cohesive architectural layers:

```
Source Repositories (Python, Java, Go, Manifests, Certificates)
   │
   ▼
[ 1. Discovery & Static Scanners ]
   ├─ Python AST Scanner (ast visitor for hashlib, cryptography, Crypto, ssl)
   ├─ Java Scanner (Regex & AST pattern matching for JCA/JCE primitives, jjwt, java-jwt)
   ├─ Go Scanner (Pattern matching for crypto/*, golang-jwt, dgrijalva/jwt-go)
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
   ├─ 7-Factor Heuristic Risk Scoring (Configurable external weights summing to 1.0)
   ├─ Missing Evidence Policy (RENORMALIZE or CONSERVATIVE)
   ├─ Mosca Readiness Index: U = (x + y) / z (AT_RISK, URGENT, SAFE)
   ├─ Migration Triage Matrix: Priority bands (CRITICAL, HIGH, MEDIUM, LOW)
   ├─ 6-State Remediation Lifecycle: DISCOVERED -> EVALUATED -> IN_PLANNING -> IN_MIGRATION -> VALIDATED -> DECOMMISSIONED
   └─ Heterogeneous GATv2 Model (HeteroData PyG message-passing, LOPO evaluation, explainability hooks)
   │
   ▼
[ 4. Defensive Security & Multi-User Isolation ]
   ├─ User Authentication: bcrypt (12 rounds, 72-byte limit) + PyJWT (HS256) bearer tokens
   ├─ Session Security: Server-side token revocation blacklist (invalidated_tokens SQLite table)
   ├─ Project Isolation: User-scoped project ownership across CRUD, scan, and export operations
   ├─ Benchmark Whitelist: Public research datasets (LEGACY_BENCHMARK_PROJECTS) read-accessible without silent claiming
   └─ Production Hardening: AGILEGRAPH_ALLOW_ANONYMOUS disabled by default, strictly rejected in production
   │
   ▼
[ 5. Presentation & Analytics ]
   ├─ Public Landing Page (/) with Platform Capabilities, Workflow, and Methodology previews
   ├─ Protected React / TypeScript Web Dashboard (/app) with Force-Directed Graph Viewer
   ├─ FastAPI REST Backend + SQLite State Persistence (agilegraph_migrations.db)
   └─ Audit Exporters (Markdown & JSON) with SHA-256 Provenance Manifests
```

---

## 2. Key Capabilities

- **Automated Cryptographic Inventory**: Detects symmetric ciphers, asymmetric primitives, hash functions, key derivation functions, signature algorithms, certificates, and hardcoded secrets.
- **Typed Dependency Graph Construction**: Models software architectures as property graphs connecting code files, dependencies, endpoints, and protected secrets.
- **Deterministic 7-Factor Risk Analysis**: Combines algorithmic weakness, asset criticality, data sensitivity, internet exposure, migration difficulty, CVE presence, and library centrality.
- **Post-Quantum Urgency Modeling**: Implements Mosca's theorem ($U = \frac{x+y}{z}$) to calculate migration deadlines against quantum threat timelines.
- **6-State Remediation Tracking**: Manages cryptographic asset retirement through a state machine with append-only SQLite audit trails.
- **Evaluated GATv2 Architecture**: Employs Heterogeneous Graph Attention Networks evaluated for weak-label distillation via 8-fold Leave-One-Project-Out (LOPO) cross-validation across 520 repository assets (expert-label validation blocked).
- **Multi-Tenant User Isolation**: Guards user repositories and analysis results behind authenticated sessions with zero cross-tenant leakage.
- **Reproducible Audit Reporting**: Exports cryptographic inventories and risk assessments in structured JSON and Markdown formats with SHA-256 integrity digests.

---

## 3. Graph Schema & Edge Semantics

AgileGraph strictly enforces a 6-node, 11-edge typed property graph ontology:

### Canonical Node Types

| Node Type | Description |
| :--- | :--- |
| **`file`** | Source code file or configuration manifest. |
| **`crypto_usage`** | Specific cryptographic algorithm invocation, cipher instantiation, or key exchange call. |
| **`certificate`** | X.509 certificate, public key, or private key asset. |
| **`endpoint`** | Network service URL or communication interface. |
| **`library`** | Cryptographic software dependency or package. |
| **`sensitive_data`** | High-value secret, credential, token, or sensitive payload. |

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

AgileGraph computes a deterministic composite risk score $s \in [0.0, 1.0]$ based on 7 contextual security factors with externalized weights configured in `backend/src/config/heuristic_weights.json`:

$$\text{Base Risk} = \sum_{i=1}^{7} w_i \cdot f_i, \quad \sum_{i=1}^{7} w_i = 1.0$$

| Factor ($f_i$) | Default Weight ($w_i$) | Rationale |
| :--- | :---: | :--- |
| **`crypto_weakness`** | 0.25 | Classical broken (MD5, SHA-1, DES) or quantum-vulnerable asymmetric algorithms (RSA, ECC, DSA) are vulnerable to Shor's algorithm; small symmetric keys (AES-128) face Grover's speedup. |
| **`asset_criticality`** | 0.15 | Conservative 3-tier proxy: Explicit security modules (1.0), security-adjacent code (0.75), shared utilities with in-degree $\ge 3$ (0.50), test fixtures (0.25). |
| **`data_sensitivity`** | 0.15 | Sensitivity classification of protected secrets; long-term credentials face Store Now, Decrypt Later (SNDL) attacks. |
| **`internet_exposure`** | 0.15 | Attack surface exposure; external-facing endpoints are directly accessible to remote adversaries. |
| **`migration_difficulty`** | 0.10 | Estimated refactoring complexity based on usage fan-out, hard-coded primitives, and API entanglement. |
| **`cve_risk`** | 0.10 | Known software vulnerabilities enriched via the public Open Source Vulnerabilities (OSV) database. |
| **`library_centrality`** | 0.10 | Degree centrality and transitive dependency blast radius within the software package dependency graph. |

### Missing-Evidence Policies

When static analysis cannot observe evidence for a specific factor (e.g. offline execution without OSV connectivity):
- **`RENORMALIZE`** (Default): Observed factors are proportionally rescaled so their weights sum to 1.0, ensuring unobserved factors do not artificially depress computed risk.
- **`CONSERVATIVE`**: Missing factor evidence defaults to maximum uncertainty ($1.0$), reflecting a cautious worst-case security posture.

---

## 5. Post-Quantum Prioritization & Lifecycle

### Mosca's Theorem

Post-quantum migration urgency is quantified via Mosca's theorem:
- $x$ = Data shelf-life (years information must remain confidential)
- $y$ = Migration duration (years required to transition infrastructure to PQC)
- $z$ = Threat timeline (years until a Cryptanalytically Relevant Quantum Computer emerges)

$$\text{Urgency Ratio } U = \frac{x + y}{z}$$

| Urgency Band | Condition | Operational Meaning |
| :--- | :---: | :--- |
| **`AT_RISK`** | $U > 1.0$ | Immediate mitigation required; data will be compromised before migration completes. |
| **`URGENT`** | $0.8 \le U \le 1.0$ | Migration window is critically narrow; planning and algorithm replacement must begin. |
| **`SAFE`** | $U < 0.8$ | Sufficient runway remains before quantum threat materialization. |

### Migration Triage Matrix

Assets are triaged into four priority bands:
- **`CRITICAL`**: Quantum-vulnerable asymmetric primitives protecting high-shelf-life sensitive data on internet-exposed endpoints ($U > 1.0$).
- **`HIGH`**: Quantum-vulnerable primitives with elevated structural centrality or active deprecation notices.
- **`MEDIUM`**: Symmetric algorithms with borderline key lengths (AES-128) or internal services.
- **`LOW`**: Quantum-resistant symmetric configurations (AES-256) or test code.

### 6-State Remediation Lifecycle

AgileGraph tracks remediation transitions with SQLite persistence and an append-only audit trail:

$$\text{DISCOVERED} \longrightarrow \text{EVALUATED} \longrightarrow \text{IN\_PLANNING} \longrightarrow \text{IN\_MIGRATION} \longrightarrow \text{VALIDATED} \longrightarrow \text{DECOMMISSIONED}$$

---

## 6. Multi-Language Scanners

- **Python Scanner**: Employs Python's native `ast` module to detect cryptographic primitive invocations across `hashlib`, `cryptography`, `Crypto`, and `ssl`, extracting key sizes, cipher modes, and IV parameters.
- **Java Scanner**: Regex and AST-pattern parser targeting Java Cryptography Architecture (JCA/JCE) primitives (`Cipher.getInstance`, `KeyGenerator`, `MessageDigest`), plus JWT implementations (`io.jsonwebtoken.jjwt`, `com.auth0.jwt`).
- **Go Scanner**: AST matching targeting Go standard library packages (`crypto/tls`, `crypto/rsa`, `crypto/aes`, `crypto/elliptic`) and third-party JWT implementations.
- **Dependency Manifest Scanner**: Parses `requirements.txt`, `pom.xml`, and `go.mod` to resolve transitive dependency trees and lookup known CVE records from the local OSV cache.
- **Certificate & Secret Extractors**: Extracts PEM-encoded X.509 certificates, public/private keys, and sensitive tokens.

---

## 7. Benchmark Corpus & Reproducibility

AgileGraph evaluates multi-language coverage across 8 pinned open-source repositories (520 files):

| Language | Repository | Size Tier | Description |
| :--- | :--- | :---: | :--- |
| Python | `python_cryptography` | Large | Core cryptographic recipe library |
| Python | `python_bcrypt` | Small | Password hashing utility |
| Python | `python_itsdangerous` | Small | Cryptographic data signing |
| Java | `java_jjwt` | Large | Java JWT library |
| Java | `java_java_jwt` | Medium | Auth0 Java JWT implementation |
| Go | `go_crypto` | Large | Go supplementary cryptographic libraries |
| Go | `go_jwt` | Small | Golang JWT implementation |
| Go | `go_jwt_go` | Small | Legacy dgrijalva JWT implementation |

### Corpus Utilities
- **Build Corpus**: Run `python backend/scripts/build_corpus.py` to scan all 8 repositories, generate property graphs, compute heuristic scores, and serialize PyG `HeteroData` tensors.
- **Corpus Summary**: Run `python backend/scripts/corpus_summary.py` to inspect descriptive distributions across languages, node types, and risk levels.
- **Reproduce Evaluation**: Run `python backend/scripts/run_gatv2_evaluation.py` to re-run LOPO evaluation and baseline benchmarks.

---

## 8. GATv2 Graph Neural Network & Empirical Evaluation

AgileGraph implements a Heterogeneous Graph Attention Network (GATv2) using PyTorch Geometric (`torch_geometric`) evaluated across all 8 canonical benchmark repositories ($N = 520$ file nodes) under 8-fold Leave-One-Project-Out (LOPO) cross-validation.

> [!IMPORTANT]
> **Scientific Framing: Weak-Label Distillation Evaluated | Expert-Label Validation Blocked**
> - **Evolution from Early Scaffolding**: In early architectural scaffolding, model training was deferred. In the finalized implementation (runs #29–#32), the Heterogeneous GATv2 model and all baselines **ARE fully trained to convergence with early stopping** across all 8 benchmark repositories ($N = 520$ file nodes) under 8-fold Leave-One-Project-Out (LOPO) cross-validation.
> - **Weak-Label Distillation (Evaluated)**: Target labels are derived from the deterministic 7-factor heuristic risk engine. These empirical results characterize *representation distillation* (whether GNNs or MLPs can learn to distill the multi-factor risk topology from code property graphs under cross-repository domain shift).
> - **Expert-Label Validation (Blocked)**: Validation against *independent external human cryptographer consensus panels* or *confirmed real-world cryptanalytic exploitation incidents* remains strictly **blocked** due to the absence of certified expert-annotated datasets in the open literature. No independent real-world predictive validity is claimed beyond weak-supervision distillation.
> - **Production Runtime Separation**: In live production scans, GATv2 is isolated as an architectural prototype (`ml_status: ARCHITECTURAL_PROTOTYPE`) so it cannot alter or suppress deterministic AST scanner findings.

> [!WARNING]
> **Methodological Caveat: Distillation Agreement vs. Predictive Validation**
> Because GATv2 and the MLP are trained on labels generated by AgileGraph's internal heuristic formula, all reported metrics measure **statistical agreement with the heuristic engine (distillation fidelity)**, NOT empirical predictive validation of real-world post-quantum vulnerability. If the heuristic engine contains systematic biases, an accurate model simply reproduces those biases. These numbers demonstrate representation learning over code property graphs and must not be presented as real-world security validation.

### Controlled LOPO Benchmark Results ($N = 520$ Files, Trained to Convergence)

All models and baselines are trained to convergence using inner stratified validation splits and patience-based early stopping (max 300 epochs, patience 25 for GATv2, patience 30 for MLP) across identical 8-fold LOPO cross-validation splits. Target labels are derived from the deterministic heuristic risk engine. Both pooled sample accuracy (520 files) and unweighted fold-level mean (8 folds) are reported:

| Model / Baseline Architecture | Pooled Acc (95% CI) | Unweighted Fold Mean (Std Dev) | Balanced Acc | Macro-F1 (95% CI) | HIGH Recall | HIGH Precision | Role & Empirical Finding |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Non-Graph Feature-Only MLP** | **98.08%** [96.7%, 99.2%] | 84.35% (± 34.84%) | **98.24%** | **0.9802** [0.966, 0.993] | **99.03%** (102/103) | **99.03%** (102/103) | **Feature baseline**: Directly approximates piecewise heuristic formula from local factors. |
| **Heterogeneous GATv2 (14-dim)** | **83.08%** [80.0%, 86.0%] | **89.38%** (± 14.84%) | **73.12%** | **0.7176** [0.674, 0.760] | **27.18%** (28/103) | **96.55%** (28/29) | **GNN prototype**: Message passing; starved of HIGH files on Fold 7 (trained on 4 HIGH files). |
| **Randomized-Edge GATv2 Control** | **74.81%** [71.0%, 78.3%] | 64.92% (± 30.25%) | **71.66%** | **0.6629** [0.620, 0.701] | **97.09%** (100/103) | **43.10%** (100/232) | **Graph control**: Preserves degree distribution; noise causes Fold-7 HIGH overprediction. |
| **GATv2 with Target Leakage (15-dim)**| 81.92% [78.6%, 85.0%] | 88.78% (± 15.01%) | 72.91% | 0.7167 [0.673, 0.761] | 29.13% (30/103) | 96.77% (30/31) | **Ablation check**: Evaluated with scalar `base_risk` appended to node feature vector. |
| **Static Rule Baseline** | 52.12% | 49.14% (± 35.12%) | 38.61% | 0.3567 | 24.27% (25/103) | 37.31% (25/67) | Independent AST baseline: matches raw scanner findings against PQC categories without heuristic factor inputs. |
| **Majority Class Baseline** | 22.69% | 22.69% (± 0.00%) | 14.95% | 0.1321 | 0.00% (0/103) | 0.00% (0/0) | Statistical majority floor across folds. |
| **Heuristic Teacher Baseline** | *100.0%* | *100.0%* (± 0.00%) | *100.0%* | *1.0000* | *100.0%* | *100.0%* | Tautological ceiling (source of weak supervision labels). |

*Confidence Intervals*: 95% bootstrap confidence intervals ($B = 1000$ iterations) are computed across the pooled out-of-fold node sample ($N = 520$). They characterize descriptive sample stability rather than project-level generalization uncertainty (which is reflected in the unweighted fold-level standard deviations).

### Complementary Benchmark: Stratified 5-Fold Cross-Validation ($N = 520$ Files)

To evaluate model capacity when training folds are not starved of high-risk signals, all 520 files were additionally evaluated under Stratified 5-Fold Cross-Validation (each fold contains ~55 LOW, ~28 MED, and ~21 HIGH files):

| Model / Control Architecture | Accuracy | Macro-F1 | HIGH Recall (Class 2) | HIGH Precision (Class 2) | Empirical Role & Key Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Non-Graph Feature-Only MLP** | **97.31%** | **0.9709** | **97.09%** (100/103) | **99.01%** (100/101) | Directly approximates the 7-factor piecewise formula. |
| **Heterogeneous GATv2 (14-dim)** | **84.81%** | **0.8005** | **74.76%** (77/103) | **70.00%** (77/110) | Graph attention message passing with representative HIGH training signal. |
| **Randomized-Edge GATv2 Control** | **75.19%** | **0.6770** | **65.05%** (67/103) | **52.34%** (67/128) | Permuted topology; noise degrades accuracy by 9.6% and precision by 17.7%. |

### Key Empirical Findings & Methodological Disclosures
1. **Aggregation Sensitivity & Inability to Support a Model Ranking under LOPO**:
   - Model rankings invert depending on aggregation: Non-Graph MLP achieves higher **pooled accuracy** (98.08% vs 83.08%), whereas Heterogeneous GATv2 achieves higher **unweighted fold mean** (89.38% vs 84.35%).
   - The unweighted fold mean is heavily leveraged by small repositories: `python_bcrypt` ($N = 1$ file) and `python_itsdangerous` ($N = 3$ files) together comprise only 4 files ($0.77\%$ of data), yet command **$25.0\%$ of the unweighted fold mean**. A single misclassification in `python_bcrypt` penalizes a model by $12.5\%$.
   - Fold standard deviations are high ($\pm 14.8\%$ to $\pm 34.8\%$). With $K=8$ folds, standard errors ($\approx 12\%$) swamp the differences between models. Consequently, **no definitive architectural ranking between GATv2 and MLP is statistically supportable under LOPO**.
2. **Corpus Skew: Fold-7 HIGH-Risk Starvation & Fold-5 Majority Saturation**:
   - **Fold 7 Starvation**: 99 of the 103 HIGH-risk files in the corpus ($96.1\%$) reside in `python_cryptography`. In LOPO Fold 7, the training set contains only 4 HIGH files ($1.17\%$). GATv2's 27.18% HIGH recall under LOPO is entirely an artifact of Fold 7 starvation (predicting 26/99 in Fold 7). When balanced training data is provided under Stratified 5-Fold CV, GATv2's HIGH recall rises to **74.76%** ($77/103$).
   - **Fold 5 Majority Ballast**: `java_jjwt` has 170 files ($32.7\%$ of corpus), of which 164 are Class 0 (LOW, $96.5\%$). Every model scores $\ge 97.65\%$ on Fold 5 simply by predicting the dominant class. Fold 5 provides zero discriminative signal between graph learning, random edges, or feature learning, yet heavily weights pooled accuracy.
   - Together, Fold 5 and Fold 7 account for **348 out of 520 files ($66.9\%$)**.
3. **Local Feature Formula Approximation**:
   - When trained to convergence with early stopping, the Non-Graph MLP reaches 98.08% pooled accuracy under LOPO and 97.31% under Stratified 5-Fold CV (Macro-F1 0.9709). This confirms that the 14-dimensional input (7 factors + 7 missingness masks) contains sufficient information to directly approximate the deterministic piecewise-linear heuristic formula.
4. **Continuous Score Rank Concordance**:
   - Evaluating rank agreement across all 520 assets demonstrates strong monotonic concordance with the continuous heuristic score:
     - **Continuous Heuristic Score vs. Discrete Tiers**: Spearman $\rho = 0.9090$ ($p = 5.05 \times 10^{-199}$), Kendall $\tau = 0.7950$ ($p = 1.19 \times 10^{-115}$).
     - **Out-of-Fold GATv2 Continuous Predictions vs. Heuristic**: Spearman $\rho = 0.8985$ ($p = 2.66 \times 10^{-187}$), Kendall $\tau = 0.7369$ ($p = 1.78 \times 10^{-129}$).
     - **Out-of-Fold MLP Continuous Predictions vs. Heuristic**: Spearman $\rho = 0.9497$ ($p = 2.52 \times 10^{-263}$), Kendall $\tau = 0.8476$ ($p = 1.26 \times 10^{-170}$).
5. **Multi-Seed Stability across Seeds (42, 100, 2026)**:
   - Across 3 random seeds trained to convergence with early stopping:
     - **Non-Graph MLP**: Pooled Accuracy = **$97.95\% \pm 0.22\%$** | Macro-F1 = **$0.9779 \pm 0.0031$**.
     - **Heterogeneous GATv2**: Pooled Accuracy = **$84.17\% \pm 2.40\%$** | Macro-F1 = **$0.7501 \pm 0.0565$**.
     - **Randomized-Edge GATv2**: Pooled Accuracy = **$77.82\% \pm 3.68\%$** | Macro-F1 = **$0.6915 \pm 0.0452$**.
6. **Independent AST Baseline & Three-Tier PQC Migration Taxonomy**:
   - **Independence from Heuristic Label Inputs**: Prior evaluations artificially coupled the rule baseline to continuous heuristic inputs (`crypto_weakness` and `library_centrality`). The rule baseline has been decoupled and operates directly on raw AST pattern matching findings from the code scanner.
   - **Three PQC Migration Categories**: In place of conflating classical weaknesses with quantum risk, cryptographic primitives are partitioned into three distinct operational categories:
     1. *Classically Broken*: MD5, SHA-1, DES, 3DES, RC4, Blowfish (immediate algorithmic obsolescence).
     2. *Quantum-Vulnerable*: RSA, ECC, ECDSA, ECDH, DSA, Ed25519, X25519, DH (Shor's algorithm / Mosca Harvest Now, Decrypt Later threats).
     3. *Quantum-Resistant*: AES-128/192/256, ChaCha20, SHA-256/384/512, SHA-3, HMAC, and NIST standardized PQC algorithms (ML-KEM, ML-DSA, SLH-DSA).
   - **False-Positive Elimination**: Substring matching (`"ec"`, `"des"`) has been replaced with token-aware regex word boundaries (`\b(ec|ecc)\b`, `\bdes\b`), preventing false positive matches on common code tokens (`"select"`, `"codec"`, `"description"`, `"destination"`).
7. **Paired Permutation Testing for Model Comparisons ($B = 1000$)**:
   - Paired permutation tests evaluate whether observed accuracy differences between architectures on the pooled out-of-fold sample ($N=520$) are statistically significant:
     - **GATv2 vs. Non-Graph MLP**: $|\Delta| = 15.00\%$, $p = 0.0010$ ($p < 0.001$). Feature-only MLP outperforms GATv2 on weak-label distillation.
     - **GATv2 vs. Edge-Shuffled Control**: $|\Delta| = 8.27\%$, $p = 0.0010$ ($p < 0.001$). True graph topology significantly outperforms randomized edge noise.
     - **GATv2 vs. Static Rule Baseline**: $|\Delta| = 30.96\%$, $p = 0.0010$ ($p < 0.001$). Learned GNN representations significantly outperform keyword matching.
     - **Non-Graph MLP vs. Static Rule Baseline**: $|\Delta| = 45.96\%$, $p = 0.0010$ ($p < 0.001$). Feature distillation significantly outperforms keyword matching.
     - **GATv2 vs. Target Leakage (15-dim)**: $|\Delta| = 1.15\%$, $p = 0.0230$.
8. **Engineering & Statistical Invariants**:
   - **PyG Lazy Layers**: `create_hetero_gatv2` initializes PyG lazy layers via a dummy forward pass (`initialize_lazy_layers`) before constructing the Adam optimizer, guaranteeing all parameters and momentum buffers are registered.
   - **Zero-Support Balanced Accuracy**: Balanced accuracy is computed strictly over classes with non-zero true support, preventing artificial deflation on skewed folds (conforming to scikit-learn standard).
   - **Safe PyG Deserialization**: Benchmark artifacts are safely deserialized with `weights_only=True` via PyG schema allowlisting in `torch.serialization.add_safe_globals`, eliminating pickle code execution risks.
9. **Architectural Safeguards**:
   - In production scans, cryptographic findings are cataloged 100% deterministically by AST/regex scanners and scored by the 7-factor engine. While weak-label distillation has been rigorously evaluated, expert-label validation remains blocked; thus, the PyTorch GATv2 model is isolated as an architectural prototype (`ml_status: ARCHITECTURAL_PROTOTYPE`) and cannot suppress or alter scanner findings.

---

## 9. Authentication & Multi-User Data Isolation

AgileGraph incorporates a defense-in-depth security model to ensure multi-user isolation:

```
Unauthenticated Request ──▶ [ /login | /register | / (Public Landing) ]
                                   │
                                   ▼
Authenticated Request   ──▶ [ Bearer JWT ] ──▶ [ Blacklist Check: invalidated_tokens ]
                                                     │
                                                     ▼
                                           [ Project Ownership Check ]
                                           ├─ User is owner ──▶ Access Granted (CRUD)
                                           ├─ In LEGACY_BENCHMARK_PROJECTS ──▶ Read-Only Granted
                                           └─ Unknown / Unowned / Other User ──▶ HTTP 403 Forbidden
```

### Security Highlights
- **Password Protection**: Passwords hashed using `bcrypt` (12 rounds) with an explicit 72-byte input guard to prevent truncation vulnerabilities.
- **JWT Issuance & Revocation**: 24-hour signed tokens (`HS256`). Logout invokes server-side revocation recorded in the SQLite `invalidated_tokens` table.
- **Project Ownership Enforcement**: Every project created via `/api/v1/scan` is assigned to the authenticated user. Modification, rescan, or deletion (`DELETE /api/v1/projects/{id}`) by non-owners is rejected with **HTTP 403 Forbidden**.
- **Safe Benchmark Policy**: Shared research benchmark repositories (`python_cryptography`, `agile`, etc.) are whitelisted in `LEGACY_BENCHMARK_PROJECTS` for **read-only access** by authenticated researchers, preventing silent ownership claiming.
- **Production Guardrails**: `AGILEGRAPH_ALLOW_ANONYMOUS` is disabled by default and unconditionally ignored in production (`AGILEGRAPH_ENV=production`). In production, JWT secret keys under 32 characters halt startup.

---

## 10. Public Landing Page & Web Dashboard

AgileGraph features a dual-tier web presentation built with React 19, TypeScript, Vite, and TailwindCSS:

### Public Tier
- **Landing / About Page (`/`)**: Dark-navy post-quantum cybersecurity landing page featuring:
  - Hero with NIST PQC standard indicators and call-to-actions.
  - Interactive Platform Capabilities section (`#platform`).
  - 4-Step Operational Workflow (`#how`).
  - Research & Methodology section (`#research`) detailing the heuristic engine and GATv2 model.
  - Technology Stack showcase (`#tech`).
  - Dynamic Architecture SVG diagram preview.
- **Authentication Pages (`/login`, `/register`)**: Form validation, instant feedback, and secure token lifecycle management.

### Protected Application Tier (`/app/*`)
- **Dashboard (`/app`)**: Overall risk posture, vulnerability breakdown, and inventory stats.
- **Cryptographic Inventory (`/app/inventory`)**: Searchable, filterable ledger of discovered cryptographic assets, algorithms, key sizes, and file locations.
- **Interactive Graph (`/app/graph`)**: 2D force-directed graph visualization rendering typed nodes and edge relationships with inspectable metadata.
- **Risk Analysis (`/app/risk`)**: 7-factor breakdown per asset with interactive weight sliders and missing-data policy toggle.
- **PQC Readiness (`/app/pqc`)**: Mosca theorem timeline calculator and quantum-readiness candidate list.
- **Migration Roadmap (`/app/roadmap`)**: Interactive 6-state Kanban lifecycle board with status transition controls.
- **Audit Reports (`/app/reports`)**: Configurable Markdown and JSON compliance reports with SHA-256 provenance hashes.

---

## 11. CLI Usage

The command-line interface provides automated headless scanning and reporting:

```bash
# 1. Activate virtual environment
cd backend
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows

# 2. Scan a local repository
python -m src.cli scan ../my-repo --output scan_result.json --project-id my-project

# 3. Generate a Markdown audit report
python -m src.cli report scan_result.json --output audit_report.md

# 4. Use conservative missing-data policy
python -m src.cli scan ../my-repo --missing-data-policy CONSERVATIVE --output scan_conservative.json
```

---

## 12. REST API Reference

The FastAPI backend exposes versioned endpoints documented via Swagger UI at `http://localhost:8000/docs`:

### Authentication Endpoints
| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/auth/register` | `POST` | No | Register a new user account |
| `/api/v1/auth/login` | `POST` | No | Authenticate credentials and receive Bearer JWT |
| `/api/v1/auth/me` | `GET` | Yes | Retrieve profile of authenticated caller |
| `/api/v1/auth/logout` | `POST` | Yes | Invalidate active JWT token on server |

### Core Scanner & Graph Endpoints
| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/scan` | `POST` | Yes | Trigger static scan on a repository path |
| `/api/v1/projects/{project_id}` | `DELETE` | Yes (Owner) | Delete a project and its cached artifacts |
| `/api/v1/projects/{project_id}/graph` | `GET` | Yes (Owner/Whitelisted) | Retrieve typed property graph (nodes and edges) |
| `/api/v1/projects/{project_id}/risk` | `GET` | Yes (Owner/Whitelisted) | Retrieve scored assets and factor breakdowns |
| `/api/v1/projects/{project_id}/report/json` | `GET` | Yes (Owner/Whitelisted) | Export audit report in JSON format |
| `/api/v1/projects/{project_id}/report/markdown` | `GET` | Yes (Owner/Whitelisted) | Export audit report in Markdown format |

### Product & Post-Quantum Endpoints
| Endpoint | Method | Auth Required | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/product/{project_id}/pqc-readiness` | `GET` | Yes (Owner/Whitelisted) | High-level PQC readiness coverage metrics |
| `/api/v1/product/{project_id}/crypto-inventory` | `GET` | Yes (Owner/Whitelisted) | Full cryptographic inventory table |
| `/api/v1/product/{project_id}/assets/{asset_id}/priority` | `GET` | Yes (Owner/Whitelisted) | Asset migration priority calculation |
| `/api/v1/product/{project_id}/assets/{asset_id}/roadmap` | `GET` | Yes (Owner/Whitelisted) | Current lifecycle status and transition log |
| `/api/v1/product/{project_id}/assets/{asset_id}/roadmap` | `POST` | Yes (Owner) | Transition asset to new lifecycle status |
| `/api/v1/product/mosca` | `POST` | No | Stateless Mosca readiness calculator |

---

## 13. Installation & Getting Started

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13
- Node.js 18+ and npm
- Git

### 1. Clone Repository
```bash
git clone https://github.com/spoorthi2615/agilegraph--major-project.git
cd agilegraph--major-project
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run FastAPI backend server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to explore the public landing page, create an account, or log in to access the dashboard.

### Environment Configuration

Configuration is managed via `.env` (copy from `.env.example`). Key variables include:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AGILEGRAPH_ENV` (or `ENV`) | `development` | Deployment environment (`development` or `production`). |
| `AGILEGRAPH_SECRET_KEY` | *(dev fallback)* | Secret key for JWT signing. Must be $\ge 32$ chars in production. |
| `AGILEGRAPH_ALLOW_ANONYMOUS`| `0` | Dev/test only flag to bypass auth. Ignored in production. |
| `AGILEGRAPH_AUTH_DB` | `dataset/cache/agilegraph_migrations.db` | Path to SQLite authentication and migration database. |
| `DATABASE_URL` | `sqlite:///./dataset/cache/agilegraph.db` | SQLite connection URL for scan and project data storage. |
| `AGILEGRAPH_SCAN_ROOT` | `.` | Optional directory boundary restricting static code scanning. |
| `OSV_API_URL` | `https://api.osv.dev/v1/query` | Remote OSV vulnerability intelligence endpoint. |
| `OSV_TIMEOUT_SECONDS` | `5.0` | Timeout threshold for OSV network queries. |

---

## 14. Project Directory Structure

```
agilegraph--major-project/
├── backend/
│   ├── dataset/
│   │   ├── artifacts/             # Pinned corpus artifacts and evaluation results
│   │   ├── benchmark/             # Pinned 8-repository benchmark dataset
│   │   ├── cache/                 # SQLite migration/auth DB and OSV caches
│   │   └── reference_set/         # Unit scanner regression test fixtures
│   ├── scripts/
│   │   ├── build_corpus.py        # Benchmark corpus build pipeline
│   │   ├── corpus_summary.py      # Corpus descriptive summary utility
│   │   ├── run_benchmark.py       # Pinned repository benchmark runner
│   │   └── run_gatv2_evaluation.py # GATv2 LOPO evaluation runner
│   ├── src/
│   │   ├── api/                   # FastAPI routes (auth, product, core)
│   │   ├── config/                # Heuristic weights and factor settings
│   │   ├── core/                  # Auth security core and SQLite storage
│   │   ├── graph/                 # Property graph schema, builder, validator
│   │   ├── ml/                    # GATv2 model, HeteroData converter, features
│   │   ├── pipeline/              # Orchestration, runner, reporters
│   │   ├── risk/                  # Heuristic engine, factor extractors, Mosca
│   │   ├── scanners/              # Python AST, Java, Go, manifest scanners
│   │   ├── cli.py                 # Command-line interface
│   │   └── main.py                # FastAPI app entrypoint
│   └── tests/                     # 413 passing pytest tests
├── docs/                          # Architectural specs, proposal synopsis, and benchmarks
│   ├── AGILEGRAPH_PROJECT_SYNOPSIS.pdf   # Academic proposal synopsis (PDF)
│   ├── AGILEGRAPH_PROJECT_SYNOPSIS.docx  # Academic proposal synopsis (Word)
│   ├── architecture.md
│   ├── graph_schema.md
│   ├── risk_formula.md
│   ├── product_layer.md
│   ├── dataset.md
│   ├── evaluation.md
│   ├── reproducibility.md
│   ├── SCANNER_SCOPE.md
│   ├── CASE_STUDIES.md
│   ├── NIST_CONSISTENCY_REVIEW.md
│   └── ethics_authorization.md
├── frontend/                      # React 19 / TypeScript / Vite web application
│   ├── src/
│   │   ├── api/                   # Axios API client and auth headers
│   │   ├── components/            # UI components (LandingPage, Dashboard, Graph, ...)
│   │   ├── context/               # AuthContext for session management
│   │   └── tests/                 # 38 passing Vitest tests
├── .github/workflows/ci.yml       # Continuous integration workflow
├── .gitignore
├── LICENSE
└── README.md
```

---

## 15. Verification & Test Suite Status

Every component of AgileGraph is covered by automated unit, integration, and security tests:

| Test Suite | Framework | Total Tests | Passed | Skipped | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Backend Suite** | `pytest` | 417 | **413** | 4* | **100% Pass** |
| **Frontend Suite** | `vitest` | 38 | **38** | 0 | **100% Pass** |
| **Frontend Production Build** | `tsc -b && vite build` | — | **Exit 0** | 0 | **Clean** |

*\*Note: 4 skips are Windows OS symlink and FIFO limitations in pipeline filesystem isolation tests.*

### Running Verification Tests Locally

```bash
# Run all backend tests:
cd backend
python -m pytest tests -rs

# Run all frontend tests:
cd ../frontend
npm test -- --run

# Run frontend production build:
npm run build
```

---

## 16. Research Integrity & Disclaimers

- **Operational Security Guarantee**: The static scanners, property graph builder, deterministic 7-factor heuristic risk scoring engine, and Mosca migration triage are fully operational and deterministic.
- **ML Research Scope (Weak-Label Distillation Evaluated, Expert Validation Blocked)**: The Heterogeneous GATv2 model is evaluated for weak-label representation distillation under 8-fold cross-repository domain shift against heuristic risk priors. Validation against independent human expert consensus labels is blocked; the model does not claim independent prediction of real-world cryptanalytic outcomes. Heuristic risk scores and static scanner outputs remain the authoritative ground truth for production operations.
- **Academic Rigor**: All benchmarks and LOPO cross-validation metrics reflect actual code execution on the 8 pinned benchmark repositories. No synthetic expert panels or fabricated correlation statistics are included.
- **Non-Certification Notice**: AgileGraph risk scores are heuristic engineering prioritization metrics and do not constitute formal cryptographic proofs or certified security guarantees.

---

## 17. License & Citation

### License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.

### Citation
If you reference or build upon AgileGraph in academic work, please cite:

```bibtex
@misc{agilegraph2026,
  author = {Spoorthi and Sindhoora R and Nivedita V Shetty and Sujan S},
  title = {AgileGraph: Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration},
  year = {2026},
  howpublished = {\url{https://github.com/spoorthi2615/agilegraph--major-project}},
  note = {Major B.Tech Cyber Security Project, Guided by Ms. Madhushree, Department of Computer Science (Cyber Security), NMAMIT, Nitte (Deemed to be University)}
}
```
