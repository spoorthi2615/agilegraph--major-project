import pytest
from src.ml.baselines import HeuristicBaseline, RuleBasedBaseline, CBOMkitBaseline, RuleConfig
from src.graph.graph import AgileGraph

def test_heuristic_baseline_determinism():
    ag = AgileGraph()
    ag.G.add_node("file1", category="file", properties={"base_risk": 0.42, "heuristic_audit": {"v": 1}})
    
    baseline = HeuristicBaseline(ag)
    res1 = baseline.evaluate()
    res2 = baseline.evaluate()
    
    assert res1.scores == res2.scores
    assert res1.scores["file1"] == 0.42
    assert "file1" in res1.audit_trail

def test_rule_based_baseline():
    ag = AgileGraph()
    ag.G.add_node("file1", category="file", properties={})
    
    config = RuleConfig(version="1.0", rules=["rule_A"])
    baseline = RuleBasedBaseline(ag, config)
    res = baseline.evaluate()
    
    assert "file1" in res.scores
    assert res.audit_trail["config_version"] == "1.0"
    assert "example_rule" in res.audit_trail["hits"]["file1"]

def test_cbomkit_baseline():
    baseline = CBOMkitBaseline()
    res = baseline.evaluate("/tmp/repo")
    assert len(res.scores) == 0
    assert res.audit_trail["status"] == "UNAVAILABLE"
