from typing import Dict, Any, List
from .experiment import BaselineOutput, RuleConfig
from src.graph.graph import AgileGraph

class HeuristicBaseline:
    """Uses Phase 8 heuristic score."""
    def __init__(self, ag: AgileGraph):
        self.ag = ag

    def evaluate(self) -> BaselineOutput:
        scores = {}
        audit = {}
        for node, data in self.ag.G.nodes(data=True):
            if data.get("category") == "file":
                props = data.get("properties", {})
                if "base_risk" in props:
                    scores[node] = props["base_risk"]
                    audit[node] = props.get("heuristic_audit", {})
        return BaselineOutput(scores=scores, audit_trail=audit)

import re
from typing import Dict, Any, List, Tuple
from .experiment import BaselineOutput, RuleConfig
from src.graph.graph import AgileGraph

# --- PQC Migration Categorization ---
# 1. Classically Broken: Broken by classical cryptanalysis (MD5, SHA-1, DES, 3DES, RC4, etc.)
CLASSICALLY_BROKEN_ALGOS = {
    "md5", "sha1", "des", "3des", "desede", "tripledes", "rc4", "arc4", "blowfish", "rc2", "none"
}

# 2. Quantum Vulnerable (Asymmetric): Broken in polynomial time by Shor's algorithm on a CRQC
QUANTUM_VULNERABLE_ALGOS = {
    "rsa", "dsa", "ecdsa", "ecdh", "ed25519", "x25519", "dh", "diffiehellman",
    "diffie-hellman", "eddsa", "elgamal", "secp256k1", "secp384r1", "secp521r1", "prime256v1"
}

# 3. Quantum Resistant: Classical symmetric/hash primitives secure under NIST SP 800-57 / CNSA 2.0
QUANTUM_RESISTANT_ALGOS = {
    "aes", "chacha20", "sha256", "sha384", "sha512", "sha3", "hmac", "hmacsha256", "hmacsha384", "hmacsha512"
}

# 4. Post-Quantum Standardized (PQC): NIST FIPS 203/204/205/206 quantum-safe algorithms
PQC_STANDARDIZED_ALGOS = {
    "kyber", "dilithium", "falcon", "sphincs", "mlkem", "mldsa", "slhdsa", "hqc", "bike"
}


def match_algo_pqc_category(alg: str) -> Tuple[str, str] | None:
    """
    Classifies a cryptographic algorithm identifier into PQC migration categories
    using token-aware word-boundary matching to prevent false substring hits.

    Prevents false substring matches:
    - 'ec' will NOT match 'select', 'security', 'echo', 'record', 'codec', 'decrypt'.
    - 'des' will NOT match 'description', 'destination', 'destroy', 'deserialize'.

    Returns (category, matched_key) or None.
    """
    if not alg:
        return None
    raw = alg.lower().strip()

    # Extract alphanumeric tokens
    tokens = set(re.findall(r'[a-zA-Z0-9]+', raw))

    # 1. Classically Broken
    for k in CLASSICALLY_BROKEN_ALGOS:
        if k in tokens or re.search(r'\b' + re.escape(k) + r'\b', raw):
            return ("CLASSICALLY_BROKEN", k)

    # 2. Quantum Vulnerable (Asymmetric Public-Key)
    for k in QUANTUM_VULNERABLE_ALGOS:
        if k in tokens or re.search(r'\b' + re.escape(k) + r'\b', raw):
            return ("QUANTUM_VULNERABLE", k)

    # Explicit word-boundary check for 'ec' / 'ecc' (must be bounded word with crypto context)
    if re.search(r'\b(ec|ecc)\b', raw) and any(w in tokens for w in ("key", "curve", "sign", "verify", "crypto", "dsa", "dh")):
        return ("QUANTUM_VULNERABLE", "ec")

    # Compound signature scheme check (e.g. SHA256withRSA)
    if "rsa" in tokens or "ecdsa" in tokens or "dsa" in tokens or "ecdh" in tokens:
        return ("QUANTUM_VULNERABLE", "asymmetric")

    # 3. Quantum Resistant (Symmetric & Secure Hashes)
    for k in QUANTUM_RESISTANT_ALGOS:
        if k in tokens or re.search(r'\b' + re.escape(k) + r'\b', raw):
            return ("QUANTUM_RESISTANT", k)

    # 4. Standardized Post-Quantum (PQC)
    for k in PQC_STANDARDIZED_ALGOS:
        if k in tokens or re.search(r'\b' + re.escape(k) + r'\b', raw):
            return ("PQC_STANDARDIZED", k)

    return None


class RuleBasedBaseline:
    """
    Explicit deterministic rules mapping raw algorithm identifiers to risk,
    categorized by post-quantum migration impact without hidden parameters.
    """
    def __init__(self, ag: AgileGraph, config: RuleConfig):
        self.ag = ag
        self.config = config

    def evaluate(self) -> BaselineOutput:
        scores = {}
        audit = {"config_version": self.config.version, "rules_applied": self.config.rules, "hits": {}}

        for node, data in self.ag.G.nodes(data=True):
            if data.get("category") == "file":
                file_score = None
                rule_hits = []

                # Check neighbors for crypto usage or libraries
                neighbors = list(self.ag.G.successors(node)) + list(self.ag.G.predecessors(node))
                has_library = False

                for neighbor in set(neighbors):
                    n_data = self.ag.G.nodes[neighbor]
                    cat = n_data.get("category")

                    if cat == "crypto_usage":
                        alg = (n_data.get("algorithm") or n_data.get("properties", {}).get("algorithm") or "").lower()
                        match = match_algo_pqc_category(alg)

                        if match:
                            category, matched_key = match
                            if category == "CLASSICALLY_BROKEN":
                                file_score = max(file_score or 0.0, 0.9)
                                rule_hits.append(f"CLASSICALLY_BROKEN_ALGO({alg})")
                                rule_hits.append(f"HIGH_RISK_ALGO({alg})")  # Compatibility alias
                            elif category == "QUANTUM_VULNERABLE":
                                file_score = max(file_score or 0.0, 0.9)
                                rule_hits.append(f"QUANTUM_VULNERABLE_ALGO({alg})")
                                rule_hits.append(f"HIGH_RISK_ALGO({alg})")  # Compatibility alias
                            elif category == "QUANTUM_RESISTANT":
                                file_score = max(file_score or 0.0, 0.3)
                                rule_hits.append(f"QUANTUM_RESISTANT_ALGO({alg})")
                                rule_hits.append(f"MED_RISK_ALGO({alg})")   # Compatibility alias
                            elif category == "PQC_STANDARDIZED":
                                file_score = max(file_score or 0.0, 0.0)
                                rule_hits.append(f"PQC_ALGO({alg})")
                        else:
                            # Unrecognized crypto usage
                            file_score = max(file_score or 0.0, 0.5)
                            rule_hits.append(f"UNKNOWN_CRYPTO({alg})")

                    elif cat == "library":
                        has_library = True

                if file_score is None and has_library:
                    file_score = 0.5
                    rule_hits.append("INDIRECT_LIBRARY_RISK")

                if file_score is not None:
                    scores[node] = file_score
                    audit["hits"][node] = rule_hits

        return BaselineOutput(scores=scores, audit_trail=audit)


