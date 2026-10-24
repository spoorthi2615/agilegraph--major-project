# AgileGraph Expert Annotation Rubric

**Version:** 2.0.0  
**Project:** Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Artifact Path:** `docs/EXPERT_ANNOTATION_RUBRIC.md`  
**Intended Audience:** Qualified Cryptography & Security Engineering Experts  

---

## Overview and Guiding Principles

This rubric defines the standardized criteria for evaluating cryptographic assets in open-source software libraries. When assessing an asset, adhere strictly to the following principles:

1. **Evidence-Based Evaluation:** Evaluate assets based solely on observable evidence provided in the asset dossier: detected cryptographic algorithms, key lengths, API call sites, certificate parameters, dependency relationships, and code snippets.
2. **No Path-Only Inferences:** **Do not infer production business criticality from file paths alone.** A file located under `/src` does not automatically warrant `HIGH` priority, nor does a utility file automatically warrant `LOW` priority without examining what cryptographic operations it executes.
3. **Preserve Epistemic Uncertainty:** If observable code evidence is ambiguous, incomplete, or refers to a generic interface whose underlying provider cannot be determined, choose `UNKNOWN`, `NOT_APPLICABLE`, or `INSUFFICIENT_EVIDENCE`.

---

## The Seven Evaluation Dimensions

Each asset must be assessed across the seven dimensions detailed below:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EVALUATION RUBRIC                                      │
├──────────────────────────┬───────────────────────────┬─────────────────────────────────┤
│ 1. Migration Priority    │ 2. Cryptographic Concern  │ 3. Sensitive Data Impact        │
│    • HIGH                │    • CLASSICAL_BROKEN     │    • CREDENTIALS_OR_SECRETS     │
│    • MEDIUM              │    • CLASSICAL_VULN_PQC   │    • PERSONAL_DATA_PII          │
│    • LOW                 │    • QUANTUM_VULN_STRONG  │    • COMMUNICATION_CONTENT      │
│    • UNKNOWN             │    • POST_QUANTUM_READY   │    • INTEGRITY_TOKEN            │
│                          │    • UNKNOWN/UNCLASSIFIED │    • INTERNAL_OR_ANCILLARY      │
│                          │    • NOT_APPLICABLE       │    • UNKNOWN/INSUFFICIENT_EVID  │
├──────────────────────────┼───────────────────────────┼─────────────────────────────────┤
│ 4. Network Exposure      │ 5. Post-Quantum Urgency   │ 6. Evidence Confidence          │
│    • INTERNET_FACING     │    • IMMEDIATE_ACTION     │    • HIGH                       │
│    • INTERNAL            │    • PLANNED_MIGRATION    │    • MEDIUM                     │
│    • NOT_APPLICABLE      │    • MONITOR              │    • LOW                        │
│    • UNKNOWN             │    • INVESTIGATE_FURTHER  │                                 │
├──────────────────────────┴───────────────────────────┴─────────────────────────────────┤
│ 7. Rationale                                                                           │
│    • Concise technical explanation citing algorithms, lines, or dependency evidence.   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Dimension 1: Post-Quantum Migration Priority (Primary Ground-Truth Label)

| Label | Definition | Operational Examples |
| :--- | :--- | :--- |
| **`HIGH`** | Critical cryptographic dependency requiring immediate or scheduled post-quantum migration. Employs classical asymmetric algorithms vulnerable to Shor's algorithm (RSA, ECC, ECDSA, DH), or broken classical algorithms (MD5, DES) protecting sensitive communications or secrets. | Key generation of RSA-2048 or ECDSA P-256 for public authentication; TLS handshake implementations; asymmetric encryption of sensitive payloads. |
| **`MEDIUM`** | Secondary cryptographic usage where post-quantum risk exists but is mitigated by ephemeral lifespans, hybrid layering, or symmetric ciphers with moderate key lengths (AES-128 under Grover's reduction). | Short-lived session signatures; AES-128 token encryption; JWT HMAC-SHA256 signing where algorithm is agile and secrets are frequently rotated. |
| **`LOW`** | Quantum-resistant symmetric primitives with large keys ($\ge 256$ bits), robust hashing for integrity only, or test-only non-security wrappers. Minimal or zero post-quantum migration urgency. | AES-256-GCM encryption; SHA-384/SHA-512 checksum hashing; PBKDF2/Argon2 password hashing with high iteration counts; non-cryptographic pseudo-random generators. |
| **`UNKNOWN`** | Observable code evidence is insufficient to ascertain cryptographic purpose, algorithm identity, or operational context. | Generic wrapper around third-party JCE provider without explicit cipher string; obfuscated native binding. |

---

### Dimension 2: Cryptographic Concern

Assesses the mathematical and algorithmic vulnerability profile:

| Category | Description | Algorithm Examples |
| :--- | :--- | :--- |
| **`CLASSICAL_BROKEN`** | Mathematically broken against conventional cryptanalysis regardless of quantum computing. | MD5, SHA-1 (for signatures), DES, 3DES, RC4, ECB mode. |
| **`CLASSICAL_VULNERABLE_PQC`** | Classically secure asymmetric cryptography completely vulnerable to Shor's algorithm ($O(\log N)$ polynomial time). | RSA, DSA, Diffie-Hellman, ECDH, ECDSA, Ed25519, X25519. |
| **`QUANTUM_VULNERABLE_STRONG`** | Classically secure symmetric cryptography subject to Grover's algorithm ($O(\sqrt{N})$ quadratic speedup). Effective security reduced to $< 128$ bits. | AES-128, Camellia-128, 2-key 3DES. |
| **`POST_QUANTUM_READY`** | NIST-standardized PQC algorithms or quantum-safe symmetric ciphers offering $\ge 128$ bits post-quantum security. | ML-KEM (Kyber), ML-DSA (Dilithium), SLH-DSA (SPHINCS+), AES-256, SHA-512, ChaCha20-Poly1305. |
| **`UNKNOWN_OR_UNCLASSIFIED`** | Algorithm string or cipher suite cannot be parsed from the call site. | Dynamic cipher lookup via configuration variable. |
| **`NOT_APPLICABLE`** | File contains no active cryptographic primitive execution. | Non-crypto data model or serialization helper. |

---

### Dimension 3: Sensitive Data Impact

Assesses the sensitivity of the information protected by the cryptographic mechanism:

| Category | Description | Examples |
| :--- | :--- | :--- |
| **`CREDENTIALS_OR_SECRETS`** | Long-term confidential secrets whose compromise yields unauthorized access. | Private keys, password storage, API secrets, master key derivation. |
| **`PERSONAL_DATA_PII`** | Personally Identifiable Information, health, financial, or user identity records. | Encrypted user profiles, credit card storage, biometric hashes. |
| **`COMMUNICATION_CONTENT`** | In-transit application data, messages, or stream payloads subject to Store-Now-Decrypt-Later (SNDL) attacks. | TLS payloads, encrypted email/chat content, VPN tunnels. |
| **`INTEGRITY_TOKEN`** | Data where authentication and non-repudiation are paramount, but confidentiality is secondary. | JWT auth headers, package checksums, git commit signatures. |
| **`INTERNAL_OR_ANCILLARY`** | Internal telemetry, cache keys, non-sensitive IDs. | Cache hash indexing, distributed trace IDs. |
| **`UNKNOWN_OR_INSUFFICIENT_EVIDENCE`** | Payload contents cannot be inferred from code context. | Generic byte buffer passed to cipher. |

---

### Dimension 4: Network Exposure

| Category | Description | Examples |
| :--- | :--- | :--- |
| **`INTERNET_FACING`** | Directly callable or accessible from untrusted external networks. | Public HTTP routes, public gRPC endpoints, TLS server sockets. |
| **`INTERNAL`** | Restricted to local execution, intranet, or backend service-to-service communication. | Local socket, private microservice bus, database client. |
| **`NOT_APPLICABLE`** | Library function, data structure, or offline utility with no network transport role. | Standalone hashing routine, byte serializer. |
| **`UNKNOWN`** | Network deployment context cannot be established from repository source alone. | Generic utility method capable of either client or server use. |

---

### Dimension 5: Post-Quantum Urgency

| Category | Recommended Migration Action |
| :--- | :--- |
| **`IMMEDIATE_ACTION`** | High-priority migration target due to Store-Now-Decrypt-Later (SNDL) threat to long-lived confidentiality. |
| **`PLANNED_MIGRATION`** | Scheduled migration in roadmap; authentication or short-lived confidentiality where quantum threat is bounded. |
| **`MONITOR`** | Algorithm possesses sufficient quantum resistance (e.g. AES-256); monitor NIST standard updates. |
| **`INVESTIGATE_FURTHER`** | Additional architectural context or code tracing required before action plan can be formulated. |

---

### Dimension 6: Evidence Confidence

| Confidence | Basis |
| :--- | :--- |
| **`HIGH`** | Unambiguous evidence: explicit algorithm constants, clear API call sites, key sizes, or certificates present in the file. |
| **`MEDIUM`** | Indirect evidence: algorithm name inferred from class naming or wrapper parameters; partial call context. |
| **`LOW`** | Weak cues: generic variable names (`secret`, `token`), library imports without observable call sites. |

---

### Dimension 7: Rationale Requirement

Annotators must provide a concise technical rationale (1–3 sentences) citing specific evidence:
- **Good Rationale:** *"Employs `rsa.GenerateKey(rand.Reader, 2048)` for identity key creation in `acme/acme.go:L42`. Vulnerable to Shor's algorithm; requires migration to ML-KEM or hybrid stateful signatures."*
- **Unacceptable Rationale:** *"Looks like a high risk file because it is in the src directory."*

---

## Example Evaluated Dossiers

### Example 1: High Migration Priority
```json
{
  "asset_id": "go_crypto:acme/acme.go",
  "migration_priority": "HIGH",
  "crypto_concern": "CLASSICAL_VULNERABLE_PQC",
  "sensitive_data_impact": "CREDENTIALS_OR_SECRETS",
  "exposure": "INTERNET_FACING",
  "post_quantum_urgency": "IMMEDIATE_ACTION",
  "evidence_confidence": "HIGH",
  "rationale": "Generates RSA-2048 and ECDSA P-256 account keys for ACME automated certificate management. Susceptible to classical asymmetric quantum compromise."
}
```

### Example 2: Low Migration Priority
```json
{
  "asset_id": "python_cryptography:src/cryptography/fernet.py",
  "migration_priority": "LOW",
  "crypto_concern": "QUANTUM_VULNERABLE_STRONG",
  "sensitive_data_impact": "COMMUNICATION_CONTENT",
  "exposure": "NOT_APPLICABLE",
  "post_quantum_urgency": "MONITOR",
  "evidence_confidence": "HIGH",
  "rationale": "Fernet uses AES-128 in CBC mode with HMAC-SHA256 for authenticated symmetric encryption. Symmetric primitive retains 64-bit Grover work factor; short-lived tokens, no asymmetric key exchange."
}
```

### Example 3: Unknown / Insufficient Evidence
```json
{
  "asset_id": "java_jjwt:impl/src/main/java/io/jsonwebtoken/impl/lang/Services.java",
  "migration_priority": "UNKNOWN",
  "crypto_concern": "UNKNOWN_OR_UNCLASSIFIED",
  "sensitive_data_impact": "UNKNOWN_OR_INSUFFICIENT_EVIDENCE",
  "exposure": "NOT_APPLICABLE",
  "post_quantum_urgency": "INVESTIGATE_FURTHER",
  "evidence_confidence": "LOW",
  "rationale": "Service-loader reflection utility that dynamically discovers provider implementations at runtime. No concrete cryptographic algorithm or key parameter is observable in source."
}
```
