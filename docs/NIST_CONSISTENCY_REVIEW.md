# NIST Consistency Review & Algorithm Categorization

## 1. Overview & Regulatory Grounding

AgileGraph models cryptographic weakness according to established standards from the **National Institute of Standards and Technology (NIST)** and the **Commercial National Security Algorithm Suite 2.0 (CNSA 2.0)**.

The heuristic factor `crypto_weakness` $\in [0.0, 1.0]$ assigns base weakness scores that reflect both classical cryptanalytic health and quantum vulnerability (Shor's and Grover's algorithms).

---

## 2. Algorithm Classification and Quantum Exposure Matrix

| Algorithm Family | Base Weakness Score | Primary Threat Mechanism | Quantum / Classical Security Posture | Governing Standards & References |
| :--- | :---: | :--- | :--- | :--- |
| **MD5, SHA-1** | `1.00` | Collision attack | Classically broken; zero security margin. | NIST SP 800-131A Rev. 2 (Disallowed) |
| **DES, RC4 / ARC4** | `1.00` | Practical key-exhaustion, stream bias | Classically broken; forbidden in production. | NIST SP 800-131A Rev. 2, RFC 7465 |
| **None (Unsigned)** | `1.00` | Signature bypass | Complete lack of integrity/authenticity. | RFC 7519, NIST SP 800-52 Rev. 2 |
| **RSA (1024, 2048, 3072, 4096)** | `0.90` | Shor's Algorithm | Solvable in polynomial time by Shor's algorithm ($O((\log N)^3)$) on a CRQC. Key sizes $> 2048$ provide only classical delay. | NIST IR 8547 Section 3.1, FIPS 186-5 |
| **DSA, ECDSA (P-256, P-384, P-521)** | `0.90` | Shor's Algorithm | Discrete logarithm and elliptic curve discrete log solvable in polynomial time on a CRQC. | NIST IR 8547 Section 3.1, FIPS 186-5 |
| **Ed25519, Ed448, EdDSA** | `0.90` | Shor's Algorithm | Edwards-curve discrete logarithm solvable in polynomial time on a CRQC. | NIST IR 8547 Section 3.1, RFC 8032 |
| **DH, ECDH, X25519, X448** | `0.90` | Shor's Algorithm | Diffie-Hellman key exchange vulnerable to retrospective decryption (Harvest Now, Decrypt Later). | NIST IR 8547 Section 3.1, SP 800-56A Rev. 3 |
| **3DES (Triple DES), Blowfish** | `0.80` | Sweet32 collision + Grover speedup | 64-bit block size vulnerable to birth-day collisions; Grover's algorithm halves key security ($O(2^{k/2})$). | NIST SP 800-131A Rev. 2 (Disallowed after 2023), SP 800-67 Rev. 2 |
| **AES-128** | `0.30` | Grover's Algorithm | Quadratic speedup ($O(\sqrt{N})$) reduces effective quantum security from 128 to 64 bits, which is below CNSA 2.0 requirements. | NIST IR 8547 Section 3.2, CNSA 2.0 |
| **AES-256** | `0.10` | Grover's Algorithm | Effective security reduced from 256 to 128 bits under Grover, remaining post-quantum resilient. | NIST IR 8547 Section 3.2, FIPS 197 |
| **SHA-256, HMAC-SHA256** | `0.10` | Grover / Brassard speedup | Collision resistance reduced from 128 to ~85 bits under quantum search, but preimage remains 128-bit secure. | NIST IR 8547 Section 3.2, FIPS 180-4 |
| **SHA-384, SHA-512, HMAC-SHA384/512** | `0.05` | Grover / Brassard speedup | Maintains $\ge 192$ bits of post-quantum collision/preimage resistance. | NIST IR 8547 Section 3.2, CNSA 2.0 |
| **ChaCha20** | `0.05` | Grover's Algorithm | 256-bit symmetric stream cipher maintaining 128 bits under Grover. | RFC 8439, NIST IR 8547 |
| **ML-KEM (Kyber-512/768/1024)** | `0.00` | Post-Quantum Standard | Module-Lattice-Based Key-Encapsulation Mechanism secure against classical and quantum cryptanalysis. | **FIPS 203** (Finalized Aug 2024) |
| **ML-DSA (Dilithium-44/65/87)** | `0.00` | Post-Quantum Standard | Module-Lattice-Based Digital Signature Algorithm secure against classical and quantum cryptanalysis. | **FIPS 204** (Finalized Aug 2024) |
| **SLH-DSA (SPHINCS+)** | `0.00` | Post-Quantum Standard | Stateless Hash-Based Digital Signature Standard providing conservative quantum security. | **FIPS 205** (Finalized Aug 2024) |
| **Falcon (FN-DSA)** | `0.00` | Post-Quantum Standard | Fast-Fourier lattice-based signature scheme pending final FIPS release. | NIST PQC Round 3 Selected |
| **HQC, BIKE** | `0.00` | PQC Round 4 Candidate | Code-based key encapsulation mechanisms evaluated for backup standardization. | NIST PQC Round 4 Status |

---

## 3. Mathematical Monotonicity and Ordering Assertion

AgileGraph strictly enforces the following risk hierarchy:

$$\text{PQC Standards } (0.0) < \text{AES-256 / SHA-512 } (0.05\text{--}0.10) < \text{AES-128 } (0.30) < \text{3DES } (0.80) \le \text{Shor-Vulnerable } (0.90) < \text{Broken } (1.00)$$

This monotonic ordering is asserted by unit tests in `backend/tests/risk/test_nist_consistency.py`.
