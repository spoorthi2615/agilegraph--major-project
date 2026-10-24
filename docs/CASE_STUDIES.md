# AgileGraph Architectural Case Studies

This document presents four representative case studies illustrating AgileGraph's property-graph discovery,
heuristic factor scoring, and downstream migration triage across diverse cryptographic archetypes.

---

## CASE-01: Shor-Vulnerable RSA Key Generation in Public Service

- **Archetype**: High Quantum Vulnerability + External Exposure
- **Repository**: `python_cryptography`
- **Asset Identifier**: `python_cryptography:src/cryptography/hazmat/primitives/asymmetric/rsa.py`
- **Algorithm / Primitive**: `RSA` (key_generation)
- **Network Exposure**: `INTERNET_FACING`
- **Mosca Readiness Assumption**: `AT_RISK (x=36, y=24, z=36 -> U=1.67)`
- **Base Heuristic Risk Score**: **0.88** / 1.00
- **Migration Triage Priority**: **`HIGH`**

### Architectural Context & Narrative
Direct RSA asymmetric private key generation. Under Shor's algorithm on a CRQC, integer factorization is solved in polynomial time O((log N)^3). Combined with exposure to calling endpoints, this represents critical migration urgency.

### Factor Breakdown
| Factor | Value | Rationale |
| :--- | :---: | :--- |
| `crypto_weakness` | `0.90` | RSA-2048 Shor-vulnerable |
| `data_sensitivity` | `0.80` | Private key material |
| `asset_criticality` | `0.75` | Security core implementation |
| `internet_exposure` | `1.00` | Binds external interface |
| `cve_risk` | `0.10` | Clean dependency baseline |
| `library_centrality` | `0.45` | Imported across modules |
| `migration_difficulty` | `0.70` | Stateful key exchange replacement |

**Triage Rationale**: High Priority: Critical preliminary risk (0.88) combined with AT_RISK planning urgency and INTERNET_FACING exposure.

---

## CASE-02: Legacy Broken MD5 Checksum Construction

- **Archetype**: Classically Broken Hash Function
- **Repository**: `python_itsdangerous`
- **Asset Identifier**: `python_itsdangerous:src/itsdangerous/signer.py`
- **Algorithm / Primitive**: `MD5` (hashing)
- **Network Exposure**: `INTERNAL`
- **Mosca Readiness Assumption**: `URGENT (x=12, y=12, z=30 -> U=0.80)`
- **Base Heuristic Risk Score**: **0.79** / 1.00
- **Migration Triage Priority**: **`HIGH`**

### Architectural Context & Narrative
MD5 cryptographic hash utilized in legacy message signing. MD5 is classically broken via practical collision attacks (Wang et al.) and disallowed under NIST SP 800-131A. Must be deprecated regardless of quantum timeline.

### Factor Breakdown
| Factor | Value | Rationale |
| :--- | :---: | :--- |
| `crypto_weakness` | `1.00` | MD5 classically broken collision resistance |
| `data_sensitivity` | `0.60` | Session token signature |
| `asset_criticality` | `0.75` | Token serialization core |
| `internet_exposure` | `0.20` | Internal helper module |
| `cve_risk` | `0.00` | No published CVEs |
| `library_centrality` | `0.60` | Directly called by API handlers |
| `migration_difficulty` | `0.30` | Drop-in replacement with SHA-256 |

**Triage Rationale**: High Priority: Preliminary risk is critical (0.79) due to broken hash primitive (MD5).

---

## CASE-03: High-Centrality Shared Cryptographic Utility Library

- **Archetype**: High Centrality Architectural Dependency
- **Repository**: `go_crypto`
- **Asset Identifier**: `go_crypto:ssh/common.go`
- **Algorithm / Primitive**: `ECDSA` (signature)
- **Network Exposure**: `INTERNET_FACING`
- **Mosca Readiness Assumption**: `URGENT (x=24, y=12, z=40 -> U=0.90)`
- **Base Heuristic Risk Score**: **0.81** / 1.00
- **Migration Triage Priority**: **`HIGH`**

### Architectural Context & Narrative
Shared SSH transport negotiation module with in-degree >= 12 across the repository. High centrality amplifies blast radius; migration requires coordinated protocol upgrades.

### Factor Breakdown
| Factor | Value | Rationale |
| :--- | :---: | :--- |
| `crypto_weakness` | `0.90` | ECDSA P-256 Shor-vulnerable |
| `data_sensitivity` | `0.75` | SSH transport credentials |
| `asset_criticality` | `0.75` | Security transport core |
| `internet_exposure` | `1.00` | Network listener exposed |
| `cve_risk` | `0.20` | Low dependency risk |
| `library_centrality` | `0.85` | High in-degree architectural hub |
| `migration_difficulty` | `0.80` | Protocol-level wire format changes |

**Triage Rationale**: High Priority: High preliminary risk (0.81), high centrality (0.85), and external exposure.

---

## CASE-04: Quantum-Resilient Modern Symmetric Cipher (AES-256-GCM)

- **Archetype**: Quantum-Resilient Symmetric Encryption
- **Repository**: `java_jjwt`
- **Asset Identifier**: `java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/security/AesGcmKeyAlgorithm.java`
- **Algorithm / Primitive**: `AES` (encryption)
- **Network Exposure**: `INTERNAL`
- **Mosca Readiness Assumption**: `SAFE (x=12, y=6, z=60 -> U=0.30)`
- **Base Heuristic Risk Score**: **0.32** / 1.00
- **Migration Triage Priority**: **`LOW`**

### Architectural Context & Narrative
Modern AES-256 authenticated encryption in Galois/Counter Mode. Under Grover's algorithm, effective key search complexity is 2^128, which strictly satisfies NIST/CNSA 2.0 post-quantum requirements.

### Factor Breakdown
| Factor | Value | Rationale |
| :--- | :---: | :--- |
| `crypto_weakness` | `0.10` | AES-256 resilient to Grover (128-bit quantum margin) |
| `data_sensitivity` | `0.50` | Encrypted payload data |
| `asset_criticality` | `0.50` | Shared encryption utility |
| `internet_exposure` | `0.20` | Internal helper library |
| `cve_risk` | `0.00` | Zero CVE vulnerabilities |
| `library_centrality` | `0.40` | Standard module usage |
| `migration_difficulty` | `0.20` | Compliant modern primitive |

**Triage Rationale**: Low Priority: Low base risk (0.32) and SAFE planning horizon (U=0.30).

---
