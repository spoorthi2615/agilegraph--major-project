# CBOMkit Feasibility and Infrastructure Investigation Report

## 1. Executive Summary
This investigation evaluates the feasibility of integrating **CBOMkit-Hyperion** as an external baseline for cryptographic asset discovery and risk prioritization within AgileGraph.

**Status**: **CONDITIONAL / RUNTIME BLOCKED**
- **Java Environment**: Verified (OpenJDK 17 Temurin is available).
- **Docker Environment**: Docker CLI is installed, but the **Docker Desktop daemon is inactive** (`npipe:////./pipe/dockerDesktopLinuxEngine` connection refused).
- **SonarQube Dependency**: CBOMkit-Hyperion functions as a SonarQube plugin (`sonar-cryptography-plugin`), requiring an active SonarQube Server instance and `sonar-scanner` CLI execution per repository.
- **Architectural Scope**: CBOMkit generates a static **CycloneDX Cryptographic Bill of Materials (CBOM)** cataloging detected primitives; it **does NOT generate risk rankings or migration scores**.

---

## 2. Technical Findings

### 2.1 Environmental Prerequisites
| Prerequisite | Required Version | Local System Status | Verdict |
|---|---|---|---|
| **Java Runtime** | Java 17+ | OpenJDK 17.0.8.1 (Temurin) | **Passed** |
| **Docker Engine** | Docker 20+ | Docker 29.6.1 CLI installed; **Daemon not running** | **Blocked** |
| **SonarQube Server** | Community 9.9+ / 10+ | Not installed locally; requires container deployment | **Blocked** |
| **CBOMkit Plugin** | `cbomkit-hyperion.jar` | Not bundled in repository | **External Dependency** |

### 2.2 Functional Capabilities vs. AgileGraph Baseline Requirements
1. **Inventory Generation**:
   - CBOMkit parses Java code via SonarQube AST rules to produce a standard CycloneDX v1.5/v1.6 CBOM with `crypto-asset` components.
   - It captures algorithms (e.g., RSA, AES, SHA-256) and key sizes where statically discoverable.
2. **Absence of Risk Ranking**:
   - CBOMkit is an **inventory extraction tool**, not a risk scoring or agility assessment engine.
   - It outputs no risk scores, no priority ordering, and no Mosca timeline readiness evaluation.
3. **Multi-Language Constraints**:
   - CBOMkit-Hyperion specializes primarily in Java codebases through SonarQube Java analysis.
   - AgileGraph's benchmark corpus spans Go (`go_crypto`, `go_jwt`), Python (`cryptography`, `bcrypt`), and Java (`java_jwt`, `jjwt`). Benchmarking CBOMkit across the entire corpus would result in incomplete cross-language comparisons.

---

## 3. Methodological Comparison: Baselines vs. AgileGraph

| Evaluation Dimension | Heuristic Engine | Static AST Rule Baseline | CBOMkit-Hyperion (Projected) | HeteroGATv2 (AgileGraph) |
|---|---|---|---|---|
| **Discovery Mechanism** | AST Regex Scanner | Word-bounded Regex Scanner | SonarQube Java AST Scanner | Code Property Graph Message-Passing |
| **PQC Classification** | 7-factor composite | 3-tier PQC taxonomy (Broken, Quantum-Vuln, Resistant) | Static CBOM inventory tags | Weak-supervision distillation |
| **Risk Scoring** | Continuous [0, 1] | Categorical (High/Med/Low) | None (Requires external adapter) | Multi-class logits |
| **Language Coverage** | Python, Java, Go | Python, Java, Go | Java primarily | Python, Java, Go |
| **Infrastructure Overhead** | Zero (Native Python) | Zero (Native Python) | High (SonarQube + Docker + Java) | Lightweight (PyTorch Geometric) |

---

## 4. Recommendation for B.Tech Final-Year Project
1. **Retain Current Empirical Baseline Suite**:
   - AgileGraph's existing `Static Rule Baseline` (`src/ml/baselines.py`) operates completely independently from continuous heuristic scores, uses a strict three-tier PQC taxonomy (Classically Broken, Quantum-Vulnerable, Quantum-Resistant), and supports all benchmark repositories (Go, Java, Python) without external infrastructure overhead.
2. **Documented Comparative Analysis**:
   - Include CBOMkit in the project thesis and literature review as the leading standard for CycloneDX CBOM specification, while contrasting its inventory-only scope with AgileGraph's graph-learned relational risk scoring.
3. **Future Extension**:
   - If a production environment with persistent SonarQube infrastructure is provisioned, a CBOMkit CycloneDX ingest adapter can be integrated without modifying the core graph pipeline.
