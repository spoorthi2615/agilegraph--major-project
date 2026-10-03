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
        for node, data in self.ag.G.nodes(data=True):
            if data.get("category") == "file":
                # Deterministic rule evaluation mockup
                score = 0.5 # Example fixed risk if rule hits
                scores[node] = score
                audit["hits"][node] = ["example_rule"]
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
