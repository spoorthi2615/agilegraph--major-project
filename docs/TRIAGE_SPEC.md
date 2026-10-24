# Migration Triage Specification

## 1. Scope & Purpose

This document specifies the deterministic migration triage matrix used by AgileGraph to prioritize cryptographic remediation queues.

$$\text{Priority} = f(\text{base\_risk}, \text{mosca\_urgency}, \text{exposure\_posture})$$

### Core Tenet: Downstream Planning Separation
As mandated by Section 5.5 of the AgileGraph Project Synopsis:
- **Base Risk Score** $R \in [0, 1]$ is an objective, deterministic property graph and heuristic metric reflecting algorithmic weakness, library posture, structural centrality, and detected usage patterns.
- **Mosca Urgency** and **Exposure Posture** are organizational planning parameters. They determine queue scheduling, resource allocation, and remediation sequence.
- **Under no circumstances does triage elevation alter or feed back into the base risk score.**

---

## 2. Input Dimensions

### 2.1 Base Risk Score ($R \in [0.0, 1.0]$)
Derived from the 7-factor heuristic model (`backend/src/config/heuristic_weights.json`).
- **High / Critical Risk**: $R \ge 0.75$
- **Moderate Risk**: $0.45 \le R < 0.75$
- **Low Risk**: $R < 0.45$
- **Unassessed**: $R \text{ is None}$ (e.g., missing critical evidence under non-renormalized policy)

### 2.2 Mosca Readiness Urgency ($U = (x + y) / z$)
Calculated from organizational inputs:
- $x$: Data confidentiality shelf-life / retention period
- $y$: Estimated migration time to quantum-safe alternatives
- $z$: Quantum capability horizon (organizational planning assumption, not a physical prediction)

| Urgency Band | Condition | Planning Definition |
| :--- | :--- | :--- |
| **AT_RISK** | $U > 1.0$ ($x + y > z$) | Confidentiality period plus migration exceeds estimated quantum horizon. |
| **URGENT** | $0.8 \le U \le 1.0$ | Approaches quantum horizon within a 20% safety margin. |
| **SAFE** | $U < 0.8$ | Sufficient timeline margin before estimated quantum horizon. |
| **INSUFFICIENT_DATA** | $x, y \text{ or } z \text{ missing, or } z \le 0$ | Insufficient data to evaluate horizon ratio. |

### 2.3 Exposure Posture
Determined from network endpoint static analysis or operator declaration:
- **INTERNET_FACING**: Service binds to all interfaces (`0.0.0.0`, `::`) or public endpoint.
- **INTERNAL / LOCAL / UNKNOWN**: Contained within intranet, loopback, or private boundaries.

---

## 3. Deterministic Triage Rule Matrix

| Base Risk Band | Mosca Urgency | Exposure Posture | Priority Level | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **None** | *Any* | *Any* | **NOT_ASSESSED** | Preliminary risk score could not be determined. |
| **High** ($R \ge 0.75$) | *Any* | *Any* | **HIGH** | High inherent cryptographic risk; prioritized regardless of planning horizon. |
| **Moderate** ($0.45 \le R < 0.75$) | `AT_RISK` | *Any* | **HIGH** | Elevated due to breached quantum horizon ($U > 1.0$). |
| **Moderate** ($0.45 \le R < 0.75$) | `URGENT` | `INTERNET_FACING` | **HIGH** | Elevated due to external exposure combined with approaching horizon ($0.8 \le U \le 1.0$). |
| **Moderate** ($0.45 \le R < 0.75$) | `URGENT` | Contained / Other | **MEDIUM** | Moderate risk under urgent horizon with contained network exposure. |
| **Moderate** ($0.45 \le R < 0.75$) | `SAFE` / `INSUFFICIENT` | *Any* | **MEDIUM** | Standard moderate risk remediation queue. |
| **Low** ($R < 0.45$) | `AT_RISK` | `INTERNET_FACING` | **HIGH** | Elevated from low risk due to external exposure and breached horizon. |
| **Low** ($R < 0.45$) | `AT_RISK` | Contained / Other | **MEDIUM** | Elevated from low risk due to breached quantum horizon. |
| **Low** ($R < 0.45$) | `URGENT` | `INTERNET_FACING` | **MEDIUM** | Elevated from low risk due to external exposure under urgent horizon. |
| **Low** ($R < 0.45$) | `URGENT` | Contained / Other | **LOW** | Contained exposure and low base risk; monitored under standard schedule. |
| **Low** ($R < 0.45$) | `SAFE` / `INSUFFICIENT` | *Any* | **LOW** | Lowest queue priority; deferred or standard maintenance. |

---

## 4. Tie-Breaking and Queue Sorting Order

When sorting remediation candidates within the dashboard and reporting layers:
1. **Priority Level**: `HIGH` (0) > `MEDIUM` (1) > `LOW` (2) > `NOT_ASSESSED` (3)
2. **Base Risk Score** (Descending): Higher numeric score sorted first.
3. **Mosca Urgency**: `AT_RISK` (0) > `URGENT` (1) > `INSUFFICIENT_DATA` (2) > `SAFE` (3)
4. **Asset ID** (Lexicographical ascending): Guarantees total determinism.
