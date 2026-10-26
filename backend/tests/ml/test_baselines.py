import pytest
from src.ml.baselines import HeuristicBaseline, RuleBasedBaseline, RuleConfig
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
    ag.G.add_node("usage1", category="crypto_usage", properties={"algorithm": "md5"})
    ag.G.add_edge("file1", "usage1", relationship="CONTAINS")
    
    config = RuleConfig(version="1.0", rules=["rule_A"])
    baseline = RuleBasedBaseline(ag, config)
    res = baseline.evaluate()
    
    assert "file1" in res.scores
    assert res.scores["file1"] == 0.9
    assert res.audit_trail["config_version"] == "1.0"
    assert "HIGH_RISK_ALGO(md5)" in res.audit_trail["hits"]["file1"]
    assert "CLASSICALLY_BROKEN_ALGO(md5)" in res.audit_trail["hits"]["file1"]


def test_rule_based_baseline_pqc_categories():
    """Verify distinct PQC categories: classically broken, quantum-vulnerable, and quantum-resistant."""
    ag = AgileGraph()
    ag.G.add_node("f_md5", category="file", properties={})
    ag.G.add_node("u_md5", category="crypto_usage", properties={"algorithm": "md5"})
    ag.G.add_edge("f_md5", "u_md5", relationship="CONTAINS")

    ag.G.add_node("f_rsa", category="file", properties={})
    ag.G.add_node("u_rsa", category="crypto_usage", properties={"algorithm": "rsa-4096"})
    ag.G.add_edge("f_rsa", "u_rsa", relationship="CONTAINS")

    ag.G.add_node("f_aes", category="file", properties={})
    ag.G.add_node("u_aes", category="crypto_usage", properties={"algorithm": "aes-256-gcm"})
    ag.G.add_edge("f_aes", "u_aes", relationship="CONTAINS")

    ag.G.add_node("f_kyber", category="file", properties={})
    ag.G.add_node("u_kyber", category="crypto_usage", properties={"algorithm": "mlkem-768"})
    ag.G.add_edge("f_kyber", "u_kyber", relationship="CONTAINS")

    config = RuleConfig(version="pqc-v1", rules=["all"])
    res = RuleBasedBaseline(ag, config).evaluate()

    # Classically broken: MD5
    assert res.scores["f_md5"] == 0.9
    assert any("CLASSICALLY_BROKEN" in h for h in res.audit_trail["hits"]["f_md5"])

    # Quantum vulnerable: RSA
    assert res.scores["f_rsa"] == 0.9
    assert any("QUANTUM_VULNERABLE" in h for h in res.audit_trail["hits"]["f_rsa"])

    # Quantum resistant symmetric: AES-256
    assert res.scores["f_aes"] == 0.3
    assert any("QUANTUM_RESISTANT" in h for h in res.audit_trail["hits"]["f_aes"])

    # Post-quantum standardized: ML-KEM
    assert res.scores["f_kyber"] == 0.0
    assert any("PQC_ALGO" in h for h in res.audit_trail["hits"]["f_kyber"])


def test_rule_based_baseline_no_substring_false_positives():
    """Verify that 'ec' and 'des' do NOT match non-crypto strings like 'security' or 'description'."""
    ag = AgileGraph()
    # Non-crypto strings containing 'ec' or 'des'
    ag.G.add_node("f_codec", category="file", properties={})
    ag.G.add_node("u_codec", category="crypto_usage", properties={"algorithm": "video_codec"})
    ag.G.add_edge("f_codec", "u_codec", relationship="CONTAINS")

    ag.G.add_node("f_desc", category="file", properties={})
    ag.G.add_node("u_desc", category="crypto_usage", properties={"algorithm": "payload_description"})
    ag.G.add_edge("f_desc", "u_desc", relationship="CONTAINS")

    # True DES
    ag.G.add_node("f_des", category="file", properties={})
    ag.G.add_node("u_des", category="crypto_usage", properties={"algorithm": "des-cbc"})
    ag.G.add_edge("f_des", "u_des", relationship="CONTAINS")

    config = RuleConfig(version="pqc-v1", rules=["all"])
    res = RuleBasedBaseline(ag, config).evaluate()

    # 'video_codec' should NOT trigger HIGH_RISK_ALGO from 'ec'
    assert not any("HIGH_RISK" in h for h in res.audit_trail["hits"].get("f_codec", []))
    assert not any("QUANTUM_VULNERABLE" in h for h in res.audit_trail["hits"].get("f_codec", []))

    # 'payload_description' should NOT trigger HIGH_RISK_ALGO from 'des'
    assert not any("HIGH_RISK" in h for h in res.audit_trail["hits"].get("f_desc", []))
    assert not any("CLASSICALLY_BROKEN" in h for h in res.audit_trail["hits"].get("f_desc", []))

    # True DES-CBC MUST trigger CLASSICALLY_BROKEN
    assert res.scores["f_des"] == 0.9
    assert any("CLASSICALLY_BROKEN" in h for h in res.audit_trail["hits"]["f_des"])

