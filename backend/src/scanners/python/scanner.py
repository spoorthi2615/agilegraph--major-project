"""
Python cryptographic API scanner using AST analysis.

Design principles:
  - Resolve imports and aliases explicitly before visiting calls.
  - Never infer algorithm by substring of an unrelated identifier.
  - Algorithm name is the CANONICAL token that reaches the scoring layer.
  - Key material (e.g. b'12345678') must not appear as an algorithm value.
  - EC/DSA/RSA key generation must be labelled with the correct family.
"""
import ast
from typing import List, Dict, Optional
from src.scanners.common.models import FindingRecord
from src.scanners.common.enums import AssetType, Language

# Maps (module, attr) → canonical algorithm for direct-call APIs.
# module may be an alias registered in self.module_to_base.
_HASHLIB_ATTRS = {
    "md5":    "md5",
    "sha1":   "sha1",
    "sha224": "sha224",
    "sha256": "sha256",
    "sha384": "sha384",
    "sha512": "sha512",
}

# Known cipher/key-gen modules from Crypto/Cryptodome
_CRYPTO_CIPHER_MODULES = {
    "AES":      ("aes",   "encryption"),
    "DES":      ("des",   "encryption"),
    "DES3":     ("3des",  "encryption"),
    "ARC4":     ("rc4",   "encryption"),
    "Blowfish": ("blowfish", "encryption"),
    "PKCS1_v1_5": ("rsa", "encryption"),
    "PKCS1_OAEP": ("rsa", "encryption"),
}

_CRYPTO_PUBKEY_MODULES = {
    "RSA":  ("rsa",   "key_generation"),
    "DSA":  ("dsa",   "key_generation"),
    "ECC":  ("ecdsa", "key_generation"),  # ECC in pycryptodome is ECDSA family
    "ElGamal": ("dh", "key_generation"),
}

# from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa, ed25519, ed448, x25519, x448
_CRYPTOGRAPHY_HAZMAT_ASYM = {
    "rsa":     ("rsa",   "key_generation"),
    "ec":      ("ecdsa", "key_generation"),
    "dsa":     ("dsa",   "key_generation"),
    "ed25519": ("ecdsa", "key_generation"),   # EdDSA / Curve25519
    "ed448":   ("ecdsa", "key_generation"),
    "x25519":  ("ecdh",  "key_generation"),
    "x448":    ("ecdh",  "key_generation"),
    "padding": (None,    None),               # not a primitive
}


class PythonCryptoVisitor(ast.NodeVisitor):
    def __init__(self, repository: str, filepath: str):
        self.repository = repository
        self.filepath = filepath
        self.findings: List[FindingRecord] = []

        # Maps local name → (base_module, canonical_role)
        # e.g. "h" → "hashlib"   (from import hashlib as h)
        #      "sha1" → "sha1"   (from hashlib import sha1)
        #      "DES" → "DES"     (from Crypto.Cipher import DES)
        #      "gpk" → "generate_private_key" (from ... import generate_private_key as gpk)

        self.module_alias: Dict[str, str] = {}    # local name → base module
        self.name_to_algo: Dict[str, Optional[tuple]] = {}  # local name → (alg, op) or None
        self.name_to_source_module: Dict[str, str] = {}     # local name → dotted source module

        # Which base modules are in scope
        self.target_bases = {"hashlib", "Crypto", "Cryptodome", "cryptography", "rsa", "hmac"}

    # ------------------------------------------------------------------
    # Import visitors
    # ------------------------------------------------------------------

    def visit_Import(self, node):
        for alias in node.names:
            base = alias.name.split(".")[0]
            if base in self.target_bases:
                local = alias.asname if alias.asname else alias.name
                self.module_alias[local] = base
                # Emit library finding
                self._emit_library(node.lineno, base, f"Imported {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if not node.module:
            self.generic_visit(node)
            return

        parts = node.module.split(".")
        base = parts[0]

        if base not in self.target_bases and base not in ("Crypto", "Cryptodome", "cryptography"):
            self.generic_visit(node)
            return

        self._emit_library(node.lineno, base, f"Imported from {node.module}")

        for alias in node.names:
            original = alias.name
            local = alias.asname if alias.asname else alias.name

            # Resolve what this name actually is
            algo_op = self._resolve_imported_name(node.module, original)
            self.name_to_algo[local] = algo_op
            self.name_to_source_module[local] = node.module

        self.generic_visit(node)

    def _resolve_imported_name(self, module: str, name: str) -> Optional[tuple]:
        """Return (canonical_alg, operation) or None for a name imported from module."""
        mparts = module.lower().split(".")

        # from hashlib import sha1, md5, …
        if "hashlib" in mparts:
            if name.lower() in _HASHLIB_ATTRS:
                return (_HASHLIB_ATTRS[name.lower()], "hashing")
            return None

        # from Crypto.Cipher import DES, AES, …
        if "cipher" in mparts:
            if name in _CRYPTO_CIPHER_MODULES:
                return _CRYPTO_CIPHER_MODULES[name]
            return None

        # from Crypto.PublicKey import RSA, DSA, ECC, …
        if "publickey" in mparts or "public_key" in mparts:
            if name in _CRYPTO_PUBKEY_MODULES:
                return _CRYPTO_PUBKEY_MODULES[name]
            return None

        # from Crypto.Hash import SHA1, MD5, SHA256, …
        if "hash" in mparts:
            low = name.lower().replace("-", "").replace("_", "")
            for k, v in _HASHLIB_ATTRS.items():
                if k == low:
                    return (v, "hashing")
            return None

        # from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa …
        if "asymmetric" in mparts:
            if name.lower() in _CRYPTOGRAPHY_HAZMAT_ASYM:
                return _CRYPTOGRAPHY_HAZMAT_ASYM[name.lower()]
            # generate_private_key is a function in these modules
            if name == "generate_private_key":
                return None   # resolved at call site
            return None

        # from cryptography.hazmat.primitives.hashes import SHA256, SHA1 …
        if "hashes" in mparts:
            low = name.lower().replace("-", "").replace("_", "")
            for k, v in _HASHLIB_ATTRS.items():
                if k == low:
                    return (v, "hashing")
            return None

        # from rsa import (generate, newkeys, …)
        if "rsa" in mparts:
            if name in ("generate", "newkeys", "generate_private_key"):
                return ("rsa", "key_generation")
            return None

        return None

    # ------------------------------------------------------------------
    # Call visitor
    # ------------------------------------------------------------------

    def visit_Call(self, node):
        full_name = self._get_full_name(node.func)
        if full_name:
            self._handle_call(node, full_name)
        self.generic_visit(node)

    def _handle_call(self, node: ast.Call, full_name: str):
        parts = full_name.split(".")
        base = parts[0]

        # ── hashlib.md5(), hashlib.sha1(), h.sha256()  ──────────────────
        if base in self.module_alias and self.module_alias[base] == "hashlib":
            if len(parts) >= 2:
                attr = parts[1].lower()
                # hashlib.new("sha256")
                if attr == "new" and node.args and isinstance(node.args[0], ast.Constant):
                    alg = str(node.args[0].value).lower().replace("-", "")
                    if alg in _HASHLIB_ATTRS:
                        self._emit_crypto(node, _HASHLIB_ATTRS[alg], "hashing", full_name, base)
                elif attr in _HASHLIB_ATTRS:
                    self._emit_crypto(node, _HASHLIB_ATTRS[attr], "hashing", full_name, base)
            return

        if base == "hashlib":
            if len(parts) >= 2:
                attr = parts[1].lower()
                if attr == "new" and node.args and isinstance(node.args[0], ast.Constant):
                    alg = str(node.args[0].value).lower().replace("-", "")
                    if alg in _HASHLIB_ATTRS:
                        self._emit_crypto(node, _HASHLIB_ATTRS[alg], "hashing", full_name, base)
                elif attr in _HASHLIB_ATTRS:
                    self._emit_crypto(node, _HASHLIB_ATTRS[attr], "hashing", full_name, base)
            return

        # ── jwt.encode(..., algorithm="HS256") ──────────────────────────
        if base == "jwt" or (base in self.module_alias and self.module_alias[base] == "jwt"):
            if len(parts) >= 2 and parts[-1].lower() in ("encode", "decode"):
                alg = "UNKNOWN_ALGORITHM"
                for kw in node.keywords:
                    if kw.arg == "algorithm" and isinstance(kw.value, ast.Constant):
                        alg = str(kw.value.value)
                self._emit_crypto(node, alg, "signature", full_name, base)
            return

        # ── Direct name from import: sha1(), DES.new(), rsa.generate() ──
        if base in self.name_to_algo:
            algo_op = self.name_to_algo[base]
            src_mod = self.name_to_source_module.get(base, "")

            if algo_op is not None:
                alg, op = algo_op
                if alg is None:
                    return  # e.g. padding module
                # For cipher classes: sha1() direct call → alg known
                if len(parts) == 1:
                    # Direct call like sha1(b"data")
                    self._emit_crypto(node, alg, op, full_name, src_mod.split(".")[0])
                elif len(parts) == 2 and parts[1].lower() in ("new", "generate", "newkeys", "generate_key",
                                                                "generate_private_key", "generate_parameters"):
                    # DES.new(), RSA.generate(), ECC.generate()
                    self._emit_crypto(node, alg, "key_generation" if "generat" in parts[1].lower() else op,
                                      full_name, src_mod.split(".")[0])
            else:
                # algo_op is None: name is generate_private_key, rsa.generate, etc.
                # Infer from source module
                if "rsa" in src_mod.lower():
                    self._emit_crypto(node, "rsa", "key_generation", full_name, src_mod.split(".")[0])
                elif "ec" in src_mod.lower() or "elliptic" in src_mod.lower():
                    self._emit_crypto(node, "ecdsa", "key_generation", full_name, src_mod.split(".")[0])
                elif "dsa" in src_mod.lower():
                    self._emit_crypto(node, "dsa", "key_generation", full_name, src_mod.split(".")[0])
            return
            
        # ── cryptography hazmat Hash(hashes.SHA256()) ──────────────────────────
        if base == "Hash" or (base in self.module_alias and self.module_alias[base] == "Hash"):
            if node.args and isinstance(node.args[0], ast.Call):
                alg_func = self._get_full_name(node.args[0].func)
                if alg_func:
                    lower_alg = alg_func.lower().replace("hashes.", "")
                    if lower_alg in _HASHLIB_ATTRS:
                        self._emit_crypto(node, _HASHLIB_ATTRS[lower_alg], "hashing", full_name, "cryptography")
            return

        # ── rsa.generate_private_key(65537, 1024) ───────────────────────
        if base in self.module_alias and self.module_alias[base] == "rsa":
            if len(parts) >= 2:
                fn = parts[-1].lower()
                if fn in ("newkeys", "generate", "generate_private_key"):
                    self._emit_crypto(node, "rsa", "key_generation", full_name, "rsa")
            return

        # ── Crypto/Cryptodome module-level calls ──────────────────────────
        # e.g. Cryptodome.Cipher.AES.new(...)
        lower_parts = [p.lower() for p in parts]
        if lower_parts[0] in ("crypto", "cryptodome"):
            if "cipher" in lower_parts:
                # Find the cipher name
                idx = lower_parts.index("cipher")
                if idx + 1 < len(parts):
                    cipher_name = parts[idx + 1]
                    if cipher_name in _CRYPTO_CIPHER_MODULES:
                        alg, op = _CRYPTO_CIPHER_MODULES[cipher_name]
                        self._emit_crypto(node, alg, op, full_name, parts[0])
            elif "publickey" in lower_parts or "public_key" in lower_parts:
                idx = next((i for i, p in enumerate(lower_parts) if "key" in p), -1)
                if idx != -1 and idx + 1 < len(parts):
                    key_name = parts[idx + 1]
                    if key_name in _CRYPTO_PUBKEY_MODULES:
                        alg, op = _CRYPTO_PUBKEY_MODULES[key_name]
                        self._emit_crypto(node, alg, op, full_name, parts[0])
            elif "hash" in lower_parts:
                idx = lower_parts.index("hash")
                if idx + 1 < len(parts):
                    hash_name = parts[idx + 1].lower().replace("-", "").replace("_", "")
                    if hash_name in _HASHLIB_ATTRS:
                        self._emit_crypto(node, _HASHLIB_ATTRS[hash_name], "hashing", full_name, parts[0])

    def _emit_crypto(self, node: ast.Call, algorithm: str, operation: str, api: str, library: str):
        self.findings.append(FindingRecord(
            asset_type=AssetType.CRYPTO_USAGE,
            repository=self.repository,
            file=self.filepath,
            line=node.lineno,
            language=Language.PYTHON,
            library=library,
            api=f"{api}()",
            algorithm=algorithm,
            operation=operation,
            evidence=f"Called {api}()",
            confidence=1.0,
            extra=self._extract_key_size(node),
        ))

    def _emit_library(self, lineno: int, base: str, evidence: str):
        self.findings.append(FindingRecord(
            asset_type=AssetType.LIBRARY,
            repository=self.repository,
            file=self.filepath,
            line=lineno,
            language=Language.PYTHON,
            library=base,
            evidence=evidence,
            confidence=1.0,
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_full_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_full_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return ""

    def _extract_key_size(self, node: ast.Call) -> dict:
        """
        Extract numeric key size from keyword or positional arguments.
        Only integers/floats are accepted — never strings.
        """
        key_size = None
        # Keywords: key_size=1024, bits=2048
        for kw in node.keywords:
            if kw.arg in ("key_size", "bits", "size") and isinstance(kw.value, ast.Constant):
                val = kw.value.value
                if isinstance(val, (int, float)):
                    key_size = val
                    break

        # Positional: generate_private_key(65537, 1024) → args[1]
        if key_size is None and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            val = node.args[1].value
            if isinstance(val, (int, float)):
                key_size = val

        # Single positional: newkeys(1024), generate(bits)
        elif key_size is None and len(node.args) == 1 and isinstance(node.args[0], ast.Constant):
            val = node.args[0].value
            if isinstance(val, (int, float)):
                key_size = val

        return {"key_size": int(key_size)} if key_size is not None else {}


def scan_python_code(repository: str, filepath: str, code: str) -> List[FindingRecord]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = PythonCryptoVisitor(repository, filepath)
    visitor.visit(tree)
    return visitor.findings
