# AgileGraph Independent Expert Review Protocol & Labelling Guide

## 1. Research Overview
**Project**: AgileGraph – Graph-Learned Crypto-Agility Risk Scoring for Post-Quantum Migration  
**Objective**: To independently assess the validity of graph-learned and heuristic risk scoring algorithms against human domain expertise in post-quantum cryptography and application security.

---

## 2. Reviewer Cohort & Panel Requirements
- **Panel Composition**: Minimum of 4 independent cybersecurity practitioners or cryptography researchers.
- **Experience Requirement**: Demonstrated competence in applied cryptography, post-quantum cryptography (PQC), or software vulnerability auditing.
- **Independence & Blinding**:
  - Reviewers evaluate cryptographic assets **blinded** to the GATv2 model outputs and the heuristic risk scores.
  - Reviewers must not consult each other during initial classification to maintain statistical independence for inter-annotator agreement.

---

## 3. Cryptographic Asset Classification Taxonomy

Reviewers classify each code asset (file containing cryptographic operations) into one of three risk tiers:

### 3.1 HIGH Risk (Immediate Migration Priority)
- **Quantum-Vulnerable Asymmetric Primitives**:
  - RSA (all key lengths, including RSA-2048, RSA-3072, RSA-4096) used for key exchange, encryption, or digital signatures. Susceptible to polynomial-time factorization via Shor's algorithm on a Cryptanalytically Relevant Quantum Computer (CRQC).
  - Elliptic Curve Cryptography (ECC, ECDSA, ECDH, Ed25519, X25519, secp256k1).
  - Classical Discrete Logarithm (Diffie-Hellman, DSA).
  - "Harvest Now, Decrypt Later" (HNDL) exposure: Data protected by these schemes with a confidentiality lifetime extending into the quantum capability horizon.
- **Classically Broken Primitives in Security Paths**:
  - MD5, SHA-1 used in signature verification or integrity checks.
  - DES, 3DES, RC4, Blowfish.

### 3.2 MEDIUM Risk (Scheduled Migration / Defense-in-Depth)
- **Symmetric Primitives with Constrained Margins**:
  - AES-128 or legacy block ciphers with short key lengths susceptible to Grover's quantum search speedup ($O(\sqrt{N})$), where migration to AES-256 or ChaCha20 is recommended.
- **Intermediate Exposure Assets**:
  - Primitives operating in internal or restricted network environments where immediate external exposure is limited.
  - Hybrid or transitional deployments lacking complete post-quantum encapsulation.
- **Ambiguous or Indirect Usage**:
  - Wrapper utilities and abstraction layers with high architectural centrality where replacement requires systemic refactoring.

### 3.3 LOW Risk (Post-Quantum Resilient / Negligible Vulnerability)
- **Standard Post-Quantum Primitives**:
  - NIST FIPS 203 (ML-KEM / Kyber), FIPS 204 (ML-DSA / Dilithium), FIPS 205 (SLH-DSA / SPHINCS+).
  - Hybrid quantum-safe key exchange algorithms.
- **Quantum-Resistant Symmetric Primitives**:
  - AES-256 (Grover's algorithm reduces effective security from 256 bits to 128 bits, which remains computationally infeasible).
  - SHA-256, SHA-384, SHA-512, SHA-3, HMAC with 256+ bit security.
- **Non-Security or Isolated Operations**:
  - Cryptographic hash functions used strictly for non-adversarial hash-map distribution or deterministic cache keys.

---

## 4. Evaluation Workflow

1. **Asset Sample**: A stratified sample of 150–200 cryptographic asset files selected from benchmark repositories across Python, Java, and Go.
2. **Reviewer Inputs**:
   - `assigned_risk_category`: `LOW`, `MEDIUM`, or `HIGH`.
   - `confidence`: Confidence score in $[0.0, 1.0]$.
   - `rationale`: Concise justification referencing primitive weakness, exposure, or data lifetime.
3. **Storage**: Annotations are collected in individual JSON files matching `annotation_template.json` and committed under `dataset/expert_annotations/submissions/`.

---

## 5. Statistical Agreement & Validation Metrics

AgileGraph evaluates expert annotations using:
1. **Fleiss' Kappa ($\kappa_{\text{Fleiss}}$)**: Inter-annotator agreement across the entire multi-reviewer panel.
2. **Weighted Cohen's Kappa ($\kappa_{\text{linear}}$)**: Pairwise agreement penalizing ordinal distance (LOW vs HIGH incurs a heavier penalty than LOW vs MEDIUM).
3. **Consensus Adjudication**: Majority consensus voting with conservative tie-breaking (highest risk precedence).
4. **Macro-F1 & Bootstrap Confidence Intervals**: Model and baseline predictions evaluated against the adjudicated expert consensus with 95% bootstrap confidence intervals ($B = 1,000$).

