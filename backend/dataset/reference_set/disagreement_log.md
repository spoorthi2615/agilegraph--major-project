# Scanner Reference Benchmark Fixture Design & Edge-Case Rationale

This document records the design decisions and syntax edge cases evaluated during curation of the 15 scanner reference benchmark test fixtures, explaining why specific tricky patterns are classified as true positives or negative false-positive guards.

> [!NOTE]
> **Provenance & Purpose**  
> These entries reflect developer-defined regression test design decisions to ensure scanners avoid common AST/regex pitfalls (such as matching comments, string variables, or unrelated method names sharing cryptographic keywords). They do not represent an external multi-annotator human consensus panel.

| Item ID | Snippet Pattern | Primary Risk of Misclassification | Expected Label | Resolution & Design Rationale |
| :--- | :--- | :--- | :---: | :--- |
| `REF-PY-003` | `crypto_ticker = "BTC/USDT"` | Simple substring scanners might match "crypto" in variable name. | `NEGATIVE` | Variable identifier contains substring "crypto" but executes no cryptographic algorithm. AST visitor must only flag actual cryptographic API calls. |
| `REF-JV-003` | `pool.initialize(8)` | Java thread pool sizing method sharing `.initialize(int)` signature with `KeyPairGenerator`. | `NEGATIVE` | Concurrency pool configuration must not be attached to cryptographic key sizing heuristics. |
| `REF-GO-005` | `// rsa.GenerateKey(rand.Reader, 2048)` | Regex matching might trigger on commented source code. | `NEGATIVE` | Commented code in documentation or dead blocks must be ignored by AST scanners. |
| `REF-JV-004` | `new SecureRandom()` | CSPRNG initialization lacks explicit algorithm cipher name parameter. | `crypto_usage` | Direct constructor instantiation of CSPRNG produces cryptographic entropy. Correctly classified as `crypto_usage` (operation: `random`). |
| `REF-PY-005` | `def calculate_md5_cache_key(): ...` | Function name mentions MD5 but executable body is commented out mock. | `NEGATIVE` | Function names alone without active API invocations must not generate false positives. |
