# AgileGraph Product Layer & Migration Triage Specification

This document specifies the product presentation and downstream planning capabilities built around the AgileGraph analysis engine, including the deterministic migration triage matrix, Mosca urgency evaluation, and remediation lifecycle management.

---

## 1. Research Engine vs. Product Layer Separation

As mandated by Section 5.5 of the AgileGraph Project Synopsis, AgileGraph enforces a strict architectural separation between core risk analysis and downstream planning:
$$\text{Base Risk} \neq \text{PQC Readiness} \neq \text{Mosca Urgency} \neq \text{Migration Priority} \neq \text{Remediation Lifecycle State}$$

- **Base Risk Score ($R \in [0.0, 1.0]$)**: An objective, deterministic property graph and heuristic metric reflecting algorithmic weakness, library posture, structural centrality, and detected usage patterns.
- **Mosca Urgency ($U = (x+y)/z$) and Exposure Posture**: Organizational planning parameters that govern remediation scheduling, team assignment, and resource allocation.
- **Strict One-Way Dependency**: Under no circumstances does triage elevation, Mosca urgency, or roadmap state alter or feed back into the base risk score or graph topology.

---

## 2. Core Product Capabilities

### 2.1 Preliminary Heuristic Risk
Provides an explainable, auditable risk assessment based on static analysis heuristics and property graph topology across 7 factors.

### 2.2 Post-Quantum Cryptographic (PQC) Inventory & Evidence Summary
Provides an asset-level inventory detailing:
- Total evaluated cryptographic assets across files, ciphers, certificates, endpoints, and dependencies.
- Breakdown of quantum-vulnerable primitives (e.g., RSA, DSA, ECDSA, ECDH) vs. quantum-safe alternatives (e.g., ML-KEM, ML-DSA, AES-256).
- Missing-data policy tracking (`RENORMALIZE` vs. `CONSERVATIVE`).

---

## 3. Mosca Planning Urgency Assessment

Post-quantum migration urgency is quantified via Mosca's theorem:
- $x$ = Data confidentiality shelf-life (years information must remain confidential).
- $y$ = Migration duration (years required to transition infrastructure to PQC).
- $z$ = Threat timeline (years until a Cryptanalytically Relevant Quantum Computer emerges).

$$\text{Urgency Ratio } U = \frac{x + y}{z}$$

*Note: $z$ is explicitly a configurable planning assumption provided by the operator, not a physical forecast by AgileGraph.*

| Urgency Band | Condition | Planning Definition |
| :--- | :---: | :--- |
| **`AT_RISK`** | $U > 1.0$ ($x + y > z$) | Confidentiality period plus migration exceeds estimated quantum horizon; data will be compromised before migration completes. |
| **`URGENT`** | $0.8 \le U \le 1.0$ | Approaches quantum horizon within a 20% safety margin; migration planning must begin immediately. |
| **`SAFE`** | $U < 0.8$ | Sufficient runway remains before estimated quantum capability emergence. |
| **`INSUFFICIENT_DATA`** | $x, y \text{ or } z \text{ missing, or } z \le 0$ | Planning inputs incomplete; horizon ratio cannot be computed. |

---

## 4. Deterministic Migration Triage Matrix

The migration triage engine combines base risk, Mosca planning urgency, and network exposure posture to sort assets into an actionable queue:
$$\text{Priority} = f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$$

### 4.1 Input Dimensions
1. **Base Risk Band ($R \in [0.0, 1.0]$)**:
   - High: $R \ge 0.75$
   - Moderate: $0.45 \le R < 0.75$
   - Low: $R < 0.45$
   - None: $R \text{ is None}$ (unassessed asset)
2. **Mosca Urgency**: `AT_RISK`, `URGENT`, `SAFE`, `INSUFFICIENT_DATA`
3. **Exposure Posture**: `INTERNET_FACING` (bound to `0.0.0.0`, `::`, or public route) vs. `CONTAINED` (internal/loopback)

### 4.2 Triage Rule Matrix

| Base Risk Band | Mosca Urgency | Exposure Posture | Priority Level | Rationale |
| :--- | :--- | :--- | :---: | :--- |
| **None** | *Any* | *Any* | **`NOT_ASSESSED`** | Preliminary risk score could not be determined. |
| **High** ($R \ge 0.75$) | *Any* | *Any* | **`HIGH`** | High inherent cryptographic risk; prioritized regardless of planning horizon. |
| **Moderate** ($0.45 \le R < 0.75$) | `AT_RISK` | *Any* | **`HIGH`** | Elevated due to breached quantum horizon ($U > 1.0$). |
| **Moderate** ($0.45 \le R < 0.75$) | `URGENT` | `INTERNET_FACING` | **`HIGH`** | Elevated due to external exposure combined with approaching horizon. |
| **Moderate** ($0.45 \le R < 0.75$) | `URGENT` | Contained / Other | **`MEDIUM`** | Moderate risk under urgent horizon with contained network exposure. |
| **Moderate** ($0.45 \le R < 0.75$) | `SAFE` / `INSUFFICIENT` | *Any* | **`MEDIUM`** | Standard moderate risk remediation queue. |
| **Low** ($R < 0.45$) | `AT_RISK` | `INTERNET_FACING` | **`HIGH`** | Elevated from low risk due to external exposure and breached horizon. |
| **Low** ($R < 0.45$) | `AT_RISK` | Contained / Other | **`MEDIUM`** | Elevated from low risk due to breached quantum horizon. |
| **Low** ($R < 0.45$) | `URGENT` | `INTERNET_FACING` | **`MEDIUM`** | Elevated from low risk due to external exposure under urgent horizon. |
| **Low** ($R < 0.45$) | `URGENT` | Contained / Other | **`LOW`** | Contained exposure and low base risk; standard monitoring schedule. |
| **Low** ($R < 0.45$) | `SAFE` / `INSUFFICIENT` | *Any* | **`LOW`** | Lowest queue priority; deferred or routine maintenance. |

### 4.3 Tie-Breaking & Queue Sorting Order
When sorting remediation candidates within dashboard views and audit reports, determinism is strictly maintained:
1. **Priority Level**: `HIGH` (0) > `MEDIUM` (1) > `LOW` (2) > `NOT_ASSESSED` (3)
2. **Base Risk Score** (Descending): Higher numeric score sorted first.
3. **Mosca Urgency**: `AT_RISK` (0) > `URGENT` (1) > `INSUFFICIENT_DATA` (2) > `SAFE` (3)
4. **Asset ID** (Lexicographical ascending): Guarantees repeatable ordering across runs.

---

## 5. 6-State Remediation Lifecycle & Persistence

AgileGraph tracks cryptographic migration transitions with SQLite persistence and an append-only audit log:

$$\text{DISCOVERED} \longrightarrow \text{EVALUATED} \longrightarrow \text{IN\_PLANNING} \longrightarrow \text{IN\_MIGRATION} \longrightarrow \text{VALIDATED} \longrightarrow \text{DECOMMISSIONED}$$

- **`DISCOVERED`**: Initial state upon scanner detection.
- **`EVALUATED`**: Cryptographic factors and base risk calculated.
- **`IN_PLANNING`**: Assigned to an organizational migration sprint or queue.
- **`IN_MIGRATION`**: Code refactoring or PQC library transition underway.
- **`VALIDATED`**: Rescanned and verified quantum-safe by static analysis.
- **`DECOMMISSIONED`**: Legacy vulnerable primitive removed or disabled.

*Note: Lifecycle transitions are user-managed governance assertions persisted in `backend/dataset/cache/agilegraph_migrations.db` with user ID, timestamp, and audit logging.*
