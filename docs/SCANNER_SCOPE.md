# AgileGraph Static Scanner Scope Specification

## 1. Overview & Architectural Scope

AgileGraph performs deterministic static discovery of cryptographic usage across multi-language source code repositories. Supported languages in current scope are:
- **Python** (via AST semantic visitor)
- **Java** (via regex pattern matching with variable tracking & context resolution)
- **Go** (via regex pattern matching and package import resolution)

In addition to language source scanners, AgileGraph executes:
- **Dependency Manifest Scanners**: `requirements.txt`, `pom.xml`, `go.mod`.
- **Certificate & Key Scanners**: Inline PEM headers, X.509 certificates, private keys.
- **Endpoint Scanners**: Server interface binds (`0.0.0.0`, port numbers, route decorators).
- **Sensitive Data Scanners**: High-entropy tokens, passwords, private keys, API secrets.

---

## 2. Python Cryptographic Scanner Scope

**Mechanism**: `backend/src/scanners/python/scanner.py` utilizes Python's native `ast` module to resolve module aliases, function aliases, and direct method invocations.

| Library / Module | Target API / Class | Canonical Algorithm | Operation | Key Size Extraction |
| :--- | :--- | :--- | :--- | :--- |
| `hashlib` | `md5()`, `sha1()`, `sha224()`, `sha256()`, `sha384()`, `sha512()` | Matching name | `hashing` | N/A |
| `hashlib` | `new("md5")`, `new("sha256")`, etc. | Extracted literal | `hashing` | N/A |
| `hmac` | `new(...)`, `HMAC(...)` | Inherited / `hmac` | `hashing` | N/A |
| `Crypto.Cipher` / `Cryptodome.Cipher` | `AES.new(...)` | `aes` | `encryption` | Resolved from key length if constant |
| `Crypto.Cipher` / `Cryptodome.Cipher` | `DES.new(...)`, `DES3.new(...)` | `des`, `3des` | `encryption` | 56 / 112 / 168 |
| `Crypto.Cipher` / `Cryptodome.Cipher` | `ARC4.new(...)`, `Blowfish.new(...)` | `rc4`, `blowfish` | `encryption` | N/A |
| `Crypto.PublicKey` / `Cryptodome.PublicKey`| `RSA.generate(N)` | `rsa` | `key_generation` | First positional integer argument |
| `Crypto.PublicKey` / `Cryptodome.PublicKey`| `DSA.generate(N)` | `dsa` | `key_generation` | Positional integer |
| `Crypto.PublicKey` / `Cryptodome.PublicKey`| `ECC.generate(...)` | `ecdsa` | `key_generation` | N/A |
| `cryptography.hazmat.primitives.asymmetric.rsa` | `generate_private_key(public_exponent, key_size)` | `rsa` | `key_generation` | Keyword `key_size` or positional |
| `cryptography.hazmat.primitives.asymmetric.ec` | `generate_private_key(curve)` | `ecdsa` | `key_generation` | Curve name (e.g., SECP256R1 -> 256) |
| `cryptography.hazmat.primitives.asymmetric.dsa` | `generate_private_key(key_size)` | `dsa` | `key_generation` | Integer argument |
| `cryptography.hazmat.primitives.asymmetric.ed25519` | `Ed25519PrivateKey.generate()` | `ecdsa` | `key_generation` | 256 |
| `cryptography.hazmat.primitives.asymmetric.x25519` | `X25519PrivateKey.generate()` | `ecdh` | `key_generation` | 256 |
| `cryptography.hazmat.primitives.ciphers` | `Cipher(algorithms.AES(key), ...)` | `aes` | `encryption` | Inferred from key |
| `cryptography.hazmat.primitives.ciphers` | `Cipher(algorithms.TripleDES(key), ...)` | `3des` | `encryption` | 192 |

---

## 3. Java Cryptographic Scanner Scope

**Mechanism**: `backend/src/scanners/java/scanner.py` uses multi-line regex patterns with variable-name tracking to link algorithm instances with `.initialize(keySize)` calls across lines.

| Library / Package | Target API / Method | Target Algorithms | Operation | Variable Resolution |
| :--- | :--- | :--- | :--- | :--- |
| `javax.crypto.Cipher` | `Cipher.getInstance(algorithm)` | `AES`, `DES`, `DESede`, `RSA`, `Blowfish`, `RC4` | `encryption` | Resolves string constants and local variables |
| `java.security.MessageDigest` | `MessageDigest.getInstance(algorithm)` | `MD5`, `SHA-1`, `SHA-256`, `SHA-384`, `SHA-512` | `hashing` | Preserves algorithm string |
| `java.security.KeyPairGenerator` | `KeyPairGenerator.getInstance(algorithm)` | `RSA`, `DSA`, `EC`, `DiffieHellman` | `key_generation` | Tracks variable name to bind `.initialize(size)` |
| `javax.crypto.KeyGenerator` | `KeyGenerator.getInstance(algorithm)` | `AES`, `DES`, `HmacSHA256` | `key_generation` | Tracks variable name to bind `.init(size)` |
| `java.security.Signature` | `Signature.getInstance(algorithm)` | `SHA256withRSA`, `SHA1withDSA`, `SHA256withECDSA` | `signature` | Resolves algorithm string |
| `javax.crypto.Mac` | `Mac.getInstance(algorithm)` | `HmacSHA256`, `HmacSHA1`, `HmacMD5` | `hashing` | Resolves algorithm string |
| `java.security.KeyAgreement` | `KeyAgreement.getInstance(algorithm)` | `ECDH`, `DH` | `key_generation` | Resolves algorithm string |
| `java.security.SecureRandom` | `SecureRandom.getInstance(algorithm)` | `SHA1PRNG`, `NativePRNG` | `random` | Resolves algorithm string |
| `java.security.SecureRandom` | `new SecureRandom()` | `SecureRandom` | `random` | Constructor invocation |
| `io.jsonwebtoken` (jjwt) | `SignatureAlgorithm.<ENUM>` | `HS256`, `HS384`, `HS512`, `RS256`, `RS384`, `RS512`, `ES256`, `ES384`, `ES512` | `signature` | Enum matching |

---

## 4. Go Cryptographic Scanner Scope

**Mechanism**: `backend/src/scanners/go/scanner.py` matches package imports and function/method call patterns, extracting key sizes from parameters where applicable.

| Package / Import | Target API / Function | Algorithm Token | Operation | Key Size Extraction |
| :--- | :--- | :--- | :--- | :--- |
| `crypto/rsa` | `rsa.GenerateKey(reader, bits)` | `rsa` | `key_generation` | Second integer parameter |
| `crypto/rsa` | `rsa.GenerateMultiPrimeKey(reader, nprimes, bits)` | `rsa` | `key_generation` | Third integer parameter |
| `crypto/rsa` | `rsa.EncryptOAEP(...)`, `rsa.DecryptOAEP(...)` | `rsa` | `encryption` | N/A |
| `crypto/rsa` | `rsa.EncryptPKCS1v15(...)`, `rsa.DecryptPKCS1v15(...)` | `rsa` | `encryption` | N/A |
| `crypto/rsa` | `rsa.SignPSS(...)`, `rsa.VerifyPSS(...)` | `rsa` | `signature` | N/A |
| `crypto/rsa` | `rsa.SignPKCS1v15(...)`, `rsa.VerifyPKCS1v15(...)` | `rsa` | `signature` | N/A |
| `crypto/ecdsa` | `ecdsa.GenerateKey(curve, reader)` | `ecdsa` | `key_generation` | Curve parameter (e.g. `P256` -> 256) |
| `crypto/ecdsa` | `ecdsa.Sign(...)`, `ecdsa.Verify(...)` | `ecdsa` | `signature` | N/A |
| `crypto/ecdsa` | `ecdsa.SignASN1(...)`, `ecdsa.VerifyASN1(...)` | `ecdsa` | `signature` | N/A |
| `crypto/ed25519` | `ed25519.GenerateKey(...)`, `ed25519.NewKeyFromSeed(...)` | `ed25519` | `key_generation` | 256 |
| `crypto/ed25519` | `ed25519.Sign(...)`, `ed25519.Verify(...)` | `ed25519` | `signature` | N/A |
| `crypto/elliptic` | `elliptic.P224()`, `P256()`, `P384()`, `P521()` | `elliptic` | `elliptic_curve` | Associated bit size |
| `crypto/tls` | `tls.Config`, `tls.Client`, `tls.Server`, `tls.Dial` | `tls` | `tls_config` | N/A |
| `crypto/aes` | `aes.NewCipher(key)` | `aes` | `encryption` | Extracted from key length if constant |
| `crypto/des` | `des.NewCipher(key)` | `des` | `encryption` | 56 |
| `crypto/md5`, `crypto/sha1` | `md5.New()`, `md5.Sum()`, `sha1.New()`, `sha1.Sum()` | `md5`, `sha1` | `hashing` | N/A |
| `crypto/sha256`, `crypto/sha512` | `sha256.New()`, `sha512.New()` | `sha256`, `sha512` | `hashing` | N/A |
| `crypto/hmac` | `hmac.New(hasher, key)` | `hmac` | `hashing` | N/A |
| `github.com/golang-jwt/jwt` | `jwt.SigningMethodRS256`, `jwt.SigningMethodES256`, etc. | Matching suffix | `signature` | Inferred from token |

---

## 5. Explicit Scanner Non-Goals & Limitations

1. **Static Approximation**: Scanners identify cryptographic calls and constants statically. Dynamic reflection (`Class.forName(...)` with runtime variables or Go interface indirection) is not executed.
2. **Deterministic Evidence Only**: Scanners emit observations accompanied by source line numbers, file paths, and verbatim code evidence snippets. No heuristic guesses or confidence inflation occurs.
