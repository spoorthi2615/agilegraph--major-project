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

class RuleBasedBaseline:
    """Explicit deterministic rules, versioned, no hidden parameters."""
    def __init__(self, ag: AgileGraph, config: RuleConfig):
        self.ag = ag
        self.config = config

    def evaluate(self) -> BaselineOutput:
        scores = {}
        audit = {"config_version": self.config.version, "rules_applied": self.config.rules, "hits": {}}
        
        # Explicit deterministic rules mapping raw algorithm identifiers to risk
        # This acts as a naive rule-based system (e.g., standard static analysis)
        high_risk_algos = {"md5", "sha1", "des", "3des", "rc4", "rsa", "ecdsa", "ed25519", "x25519", "dsa", "ec", "none"}
        med_risk_algos = {"aes", "chacha20", "sha256", "sha384", "sha512", "hmac"}
        pqc_algos = {"kyber", "dilithium", "falcon", "sphincs"}
        
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
                        alg = n_data.get("properties", {}).get("algorithm", "").lower()
                        
                        # Apply rules
                        if any(k in alg for k in high_risk_algos):
                            file_score = max(file_score or 0.0, 0.9)
                            rule_hits.append(f"HIGH_RISK_ALGO({alg})")
                        elif any(k in alg for k in med_risk_algos):
                            file_score = max(file_score or 0.0, 0.3)
                            rule_hits.append(f"MED_RISK_ALGO({alg})")
                        elif any(k in alg for k in pqc_algos):
                            file_score = max(file_score or 0.0, 0.0)
                            rule_hits.append(f"PQC_ALGO({alg})")
                        else:
                            # Unrecognized crypto usage
                            file_score = max(file_score or 0.0, 0.5)
                            rule_hits.append(f"UNKNOWN_CRYPTO({alg})")
                            
                    elif cat == "library":
                        has_library = True
                        
                if file_score is None and has_library:
                    # File imports a library but no direct usage found
                    file_score = 0.5
                    rule_hits.append("INDIRECT_LIBRARY_RISK")
                    
                if file_score is not None:
                    scores[node] = file_score
                    audit["hits"][node] = rule_hits
                    
        return BaselineOutput(scores=scores, audit_trail=audit)

class CBOMkitBaseline:
    """Comparison interface for CBOMkit."""
    def __init__(self):
        self.available = False # CBOMkit is currently unavailable in environment

    def evaluate(self, repo_path: str) -> BaselineOutput:
        if not self.available:
            return BaselineOutput(scores={}, audit_trail={"status": "UNAVAILABLE"})
        # Implement execution when available
        return BaselineOutput(scores={}, audit_trail={"status": "EXECUTED"})
