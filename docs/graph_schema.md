# Graph Schema

## Source Specification
Based on the AgileGraph synopsis, the graph consists of the following explicitly defined elements:

**Six Node Categories (Authoritative Ontology):**

| Ontology Name (PascalCase) | Internal `AssetType` enum value | Extracted by current scanners? |
|---|---|---|
| `File` | `file` | ✅ Yes — all AST and manifest scanners |
| `CryptoUsage` | `crypto_usage` | ✅ Yes — Python, Java, Go AST scanners |
| `Certificate` | `certificate` | ❌ No — ontology supported; not extracted by current public scanners |
| `Endpoint` | `endpoint` | ❌ No — schema exists; TLS scanner is localhost-only infrastructure |
| `Library` | `library` | ✅ Yes — dependency manifest scanners |
| `SensitiveData` | `sensitive_data` | ❌ No — ontology supported; not extracted by current public scanners |

> ⚠️ The ontology supports all six node types. The current scanner corpus only instantiates `File`, `CryptoUsage`, and `Library` nodes. The absence of `Certificate`, `Endpoint`, and `SensitiveData` nodes in real scan output must not be interpreted as evidence that those categories were examined and found empty.

**Relationship Types:**
The synopsis mentions that there are **seven types of relationships**, giving examples such as:
- "this code file uses this certificate"
- "this certificate protects this data"

## Implementation Decisions
To make the prototype executable and support the GATv2 risk propagation, the following complete set of edges and properties are proposed (subject to adjustment during dataset construction):

**Proposed Edges (The 7 Types):**
1. `CONTAINS` (File -> CryptoUsage, File -> Certificate)
2. `IMPORTS` (File -> Library)
3. `USES_CERT` (CryptoUsage/File -> Certificate)
4. `PROTECTS` (Certificate -> SensitiveData, CryptoUsage -> SensitiveData)
5. `EXPOSES` (Endpoint -> Certificate, Endpoint -> CryptoUsage)
6. `VULNERABLE_TO` (Library -> CVE Node - *Future extension*) or `DEPENDS_ON` (Library -> Library)
7. `CALLS` (CryptoUsage -> Library)
