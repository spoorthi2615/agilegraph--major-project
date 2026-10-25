# Static Scanner Reference Benchmark Test Suite Protocol

## 1. Objective & Provenance Notice

This protocol defines the specification and expected syntax patterns for the 15 developer-curated scanner benchmark test fixtures across Python, Java, and Go repositories.

> [!IMPORTANT]
> **Academic Integrity & Provenance Notice**  
> The 15 reference snippets in `reference_samples.json` are **developer-authored unit regression fixtures** designed to verify that AST and regex scanners reliably detect genuine cryptographic API invocations while correctly rejecting false-positive syntactic patterns (such as comments, string literals with "crypto", and unrelated concurrency pool initialization). They do **NOT** represent an external multi-annotator human panel, empirical consensus study, or independently validated real-world ground truth.

---

## 2. Benchmark Fixture Dimensions & Schema

Each reference fixture is specified across the following attributes:

| Field | Description | Allowed Values |
| :--- | :--- | :--- |
| `item_id` | Unique reference snippet identifier | String (e.g. `REF-PY-001`) |
| `language` | Programming language of snippet | `PYTHON`, `JAVA`, `GO` |
| `code` | Source code snippet under test | String |
| `expected_category` | Target graph node category | `crypto_usage`, `certificate`, `endpoint`, `library`, `sensitive_data`, `NEGATIVE` |
| `expected_algorithm` | Exact cryptographic algorithm | e.g. `rsa`, `aes`, `ecdsa`, `sha256`, `none` |
| `expected_operation` | Cryptographic primitive operation | `key_generation`, `encryption`, `signature`, `hashing`, `random`, `tls_config`, `none` |
| `fixture_rationale` | Technical reason for classification | Free-text technical explanation |
| `consensus_label` | Adjudicated expected outcome for test runner | Category name or `NEGATIVE` |

---

## 3. Inclusion & Exclusion Rules

### Positive Criteria (True Positives)
1. **Direct API Invocation**: Verifiable instantiation or invocation of a cryptographic library primitive (e.g., `rsa.generate_private_key`, `Cipher.getInstance("AES/CBC...")`, `rsa.GenerateKey`).
2. **Key / Cert Material**: Formatted PEM/DER blocks, PKCS#1/#8 headers, or valid base64 certificate structures.
3. **Endpoint Declaration**: Network socket bind (`0.0.0.0`, port specification), framework route (`@app.get(...)`).
4. **Sensitive Data**: Hardcoded private keys, JWT signing secrets, API passwords.

### Negative Criteria (True Negatives)
1. **Incidental Naming**: Variables or identifiers containing cryptographic substrings without cryptographic operations (e.g., `crypto_ticker = "BTC/USDT"`, `exchange_name = "crypto_market"`).
2. **Commented Code**: Invocations inside comments or docstrings that are not active source code (e.g., `// rsa.GenerateKey(...)`).
3. **Non-Cryptographic Methods**: Unrelated methods sharing method names (e.g., ThreadPoolExecutor `.initialize(8)`).
4. **String Printing / Logging**: Strings containing URLs or non-cryptographic tokens printed to console.

---

## 4. Verification Workflow

The verification script (`backend/scripts/verify_scanners.py`) runs the scanners against all 15 fixtures and verifies:
1. All 9 positive fixtures are detected as True Positives ($TP = 9, FN = 0$).
2. All 6 negative edge-case fixtures are rejected as True Negatives ($TN = 6, FP = 0$).
3. The script verifies scanner regression coverage; it is not presented as an empirical claim of real-world multi-repo precision/recall.
