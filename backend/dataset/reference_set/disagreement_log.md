# Scanner Reference Set Adjudication & Disagreement Log

This document records disagreements between Labeller 1 and Labeller 2 during curation of the reference benchmark set, along with the formal consensus rationale.

| Item ID | Snippet Preview | Labeller 1 | Labeller 2 | Final Consensus | Resolution Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `REF-PY-006` | `crypto_ticker = "BTC/USDT"` | `crypto_usage` | `NEGATIVE` | `NEGATIVE` | String variable name contains substring "crypto" but performs no cryptographic operation. Correctly classified as negative example. |
| `REF-JV-004` | `pool.initialize(8)` | `crypto_usage` | `NEGATIVE` | `NEGATIVE` | Thread pool sizing method sharing `.initialize(int)` signature with KeyPairGenerator. Must not be classified as crypto key size. |
| `REF-GO-005` | `// rsa.GenerateKey(rand.Reader, 2048)` | `crypto_usage` | `NEGATIVE` | `NEGATIVE` | Commented code snippet in documentation. AST and scanner must ignore unexecuted comments. |
| `REF-JV-007` | `new SecureRandom()` | `NEGATIVE` | `crypto_usage` | `crypto_usage` | Direct constructor invocation of CSPRNG generates cryptographic entropy. Resolved as `crypto_usage` (operation: `random`). |
| `REF-PY-010` | `hashlib.sha256(b"cache_key").hexdigest()` | `crypto_usage` | `crypto_usage` | `crypto_usage` | Cryptographic hash algorithm utilized for cache key derivation. Algorithm is SHA-256 regardless of application context. |
