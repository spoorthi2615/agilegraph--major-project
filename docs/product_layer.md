# AgileGraph Product Layer

This document outlines the product capabilities built around the AgileGraph research engine. It strictly maintains the separation between verified empirical results (pending) and product-planning features.

## Research vs. Product Separation
The product layer consumes the preliminary heuristic risk score and graph topology but does **not** modify them.
*   **Risk \u2260 PQC Readiness \u2260 Mosca \u2260 Migration Priority \u2260 Roadmap State**
*   **Expert validation is pending:** The heuristic risk scores and GATv2 model require empirical validation against expert labels.
*   **GATv2 empirical training/results pending expert labels:** The graph neural network models require the pending expert consensus labels.

## 1. Preliminary Heuristic Risk
Provides an initial risk assessment based on static analysis heuristics. This is not a validated scientific score yet.

## 2. PQC Evidence/Coverage Summary
An inventory-level view of cryptographic usage, detailing total assessed assets, candidates for migration, and missing evidence. It is a coverage summary, not a scientifically validated PQC readiness score.

## 3. Mosca Planning Assessment
Evaluates the Mosca theorem:
*   `x` = data confidentiality period
*   `y` = migration time
*   `z` = quantum capability horizon

**Policy:**
*   `x + y > z` \u2192 **AT_RISK**
*   `x + y <= z` \u2192 **NOT_AT_RISK**

*Note: `z` is explicitly a configurable planning assumption provided by the user, not a scientific prediction by AgileGraph.*

## 4. Migration Priority
Combines preliminary risk and Mosca planning to sort assets into an actionable queue. 
The priority does not alter the underlying risk score.

**Policy:**
| Input | Role |
| :--- | :--- |
| **Preliminary risk** | **Primary priority signal** |
| **Mosca status** | **Planning urgency** |
| **Migration difficulty** | **Informational** |
| **Algorithm** | **Informational** |
| **Missing factors** | **Informational** |

## 5. Migration Roadmap
A user-managed state machine to track migration progress.
Valid states: `Not Assessed`, `Assessment Required`, `Migration Candidate`, `High Priority`, `Planned`, `In Progress`, `Migrated`, `Verified`.

*Note: The `Migrated` and `Verified` states are user-managed planning assertions. They do not claim that AgileGraph performed or automatically verified the migration.*
