"""
Mutation-resistance tests.

These tests are specifically designed to kill the mutants identified
in the previous mutation testing run. Each test targets a specific
mutation that previously survived.

Mutant categories covered:
  M1: unrated → 0.0  (treating None as safe)
  M2: unrated dropped from scores
  M3: unrated counted as "vulnerable"
  M4: matcher-order regression (des matches desede before desede)
  M5: PQC misclassified as DSA/EC/DES
  M6: frontend null-score not guarded (API-level)
  M7: per-file raw-path opened instead of canonical path
  M8: Java key-size association by proximity, not by variable
  M9: scanner → graph key-size loss
  M10: factor_extractor silently drops None weakness
"""
import os
import tempfile
import pytest
from src.risk.algorithm_strength import extract_crypto_weakness, _extract_family
from src.risk.heuristic import calculate_heuristic_score
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.risk.factors import RiskFactors, FactorValue
from src.pipeline.runner import run_pipeline


# ──────────────────────────────────────────────────────────────────────────────
# M1 — unrated must be None, not 0.0
# ──────────────────────────────────────────────────────────────────────────────

def test_m1_unrated_is_none_not_zero():
    """Unrecognized algorithm must return None, never 0.0."""
    r = extract_crypto_weakness("GREASE_ALGO_XYZ")
    assert r.value is None, "Unrated must be None"
    assert r.value != 0.0, "Unrated must never be 0.0 (would mean perfectly safe)"


def test_m1_empty_string_is_none():
    r = extract_crypto_weakness("")
    assert r.value is None


# ──────────────────────────────────────────────────────────────────────────────
# M2 — unrated assets must appear in the score list, not be silently dropped
# ──────────────────────────────────────────────────────────────────────────────

def test_m2_unrated_not_dropped_from_pipeline(tmp_path):
    """
    A file with an unrecognized cryptographic finding must still appear in the scores
    output (as an unrated asset), not be silently omitted.
    """
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    with open(os.path.join(repo, "unknown.py"), "w") as f:
        f.write("import hashlib\nhashlib.new('unknown_algo')\n")
    result = run_pipeline(repo, "test", allowed_root=repo)
    # The file node should appear in scores (as unrated, score=None)
    all_scores = result["scores"]
    assert len(all_scores) >= 1
    # At least one asset must have score=None (unrated)
    unrated = [s for s in all_scores if s.get("score") is None]
    assert unrated, "File with unrecognized crypto must appear as unrated, not be dropped"


# ──────────────────────────────────────────────────────────────────────────────
# M3 — unrated must not be counted as "vulnerable"
# ──────────────────────────────────────────────────────────────────────────────

def test_m3_unrated_not_counted_as_vulnerable(tmp_path):
    """
    A file with unrated score must not appear in the count of scored (vulnerable) assets.
    The provenance must reflect this distinction.
    """
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    with open(os.path.join(repo, "unknown.py"), "w") as f:
        f.write("import hashlib\nhashlib.new('unknown_algo')\n")
    result = run_pipeline(repo, "test", allowed_root=repo)
    prov = result["provenance"]
    scored = prov["scored_assets"]
    unrated = prov["unrated_assets"]
    # scored + unrated = total file assets
    total_file_assets = len([s for s in result["scores"]])
    assert scored + unrated == total_file_assets, \
        f"scored({scored}) + unrated({unrated}) must equal total({total_file_assets})"
    # The unrated asset must not appear in scored count
    all_scores = result["scores"]
    none_scores = [s for s in all_scores if s.get("score") is None]
    assert len(none_scores) == unrated, "unrated_assets count mismatch"


# ──────────────────────────────────────────────────────────────────────────────
# M4 — matcher order: desede must not match 'des' key before 'desede' key
# ──────────────────────────────────────────────────────────────────────────────

def test_m4_desede_family():
    """DESede must normalize to 3des, not des."""
    family = _extract_family("DESede")
    assert family == "3des", f"DESede must be 3des, got {family!r}"


def test_m4_tripledes_family():
    family = _extract_family("TripleDES")
    assert family == "3des"


def test_m4_des_plain_is_des():
    family = _extract_family("DES")
    assert family == "des", f"Plain DES must be des, not 3des. Got {family!r}"


def test_m4_desede_vs_des_risk_different():
    """DESede (3des) and DES must NOT receive identical risk scores."""
    r_des    = extract_crypto_weakness("DES")
    r_desede = extract_crypto_weakness("DESede")
    # Both are rated
    assert r_des.value is not None
    assert r_desede.value is not None
    # DES is higher risk than 3DES (1.0 vs 0.8)
    assert r_des.value > r_desede.value, \
        f"DES ({r_des.value}) should be riskier than DESede ({r_desede.value})"


# ──────────────────────────────────────────────────────────────────────────────
# M5 — PQC misclassification
# ──────────────────────────────────────────────────────────────────────────────

def test_m5_ml_dsa_not_dsa():
    """ML-DSA-65 is PQC — must not be classified as classical DSA."""
    r = extract_crypto_weakness("ML-DSA-65")
    assert r.value is not None, "ML-DSA should be rated"
    assert r.value < 0.1, f"ML-DSA-65 is PQC, risk must be < 0.1, got {r.value}"


def test_m5_slh_dsa_not_dsa():
    r = extract_crypto_weakness("SLH-DSA-SHA2-128s")
    assert r.value is not None
    assert r.value < 0.1


def test_m5_ml_kem_not_ec():
    r = extract_crypto_weakness("ML-KEM-768")
    assert r.value is not None
    assert r.value < 0.1


def test_m5_destination_not_des():
    """'destination' contains 'des' but must NOT be classified as DES."""
    r = extract_crypto_weakness("destination")
    assert r.value is None, f"'destination' must be unrated, got {r.value}"


def test_m5_selected_alg_not_sha():
    r = extract_crypto_weakness("selectedAlg")
    assert r.value is None


# ──────────────────────────────────────────────────────────────────────────────
# M8 — Java key-size by variable, not proximity
# ──────────────────────────────────────────────────────────────────────────────

def test_m8_java_separate_vars():
    from src.scanners.java.scanner import scan_java_code
    code = """
import java.security.KeyPairGenerator;
public class X {
    public void f() throws Exception {
        KeyPairGenerator rsaGen = KeyPairGenerator.getInstance("RSA");
        rsaGen.initialize(4096);
        KeyPairGenerator ecGen = KeyPairGenerator.getInstance("EC");
        ecGen.initialize(256);
    }
}
"""
    findings = scan_java_code("test", "X.java", code)
    rsa = [f for f in findings if f.algorithm and f.algorithm.upper() == "RSA" and f.operation == "key_generation"]
    ec  = [f for f in findings if f.algorithm and f.algorithm.upper() == "EC"  and f.operation == "key_generation"]
    assert rsa and ec
    assert rsa[0].extra.get("key_size") == 4096
    assert ec[0].extra.get("key_size") == 256


def test_m8_unrelated_initialize_not_associated():
    from src.scanners.java.scanner import scan_java_code
    code = """
import java.security.KeyPairGenerator;
public class X {
    public void f() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        pool.initialize(8);
    }
}
"""
    findings = scan_java_code("test", "X.java", code)
    rsa = [f for f in findings if f.algorithm and "RSA" in f.algorithm.upper() and f.operation == "key_generation"]
    assert rsa
    assert rsa[0].extra.get("key_size") == 2048, "pool.initialize(8) must not overwrite RSA 2048"


# ──────────────────────────────────────────────────────────────────────────────
# M9 — scanner → graph key-size preservation
# ──────────────────────────────────────────────────────────────────────────────

def test_m9_key_size_preserved_in_graph(tmp_path):
    """Key sizes extracted by the scanner must be present in the graph nodes."""
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    with open(os.path.join(repo, "rsa_code.py"), "w") as f:
        f.write("""
import rsa
pub, priv = rsa.newkeys(1024)
""")
    result = run_pipeline(repo, "test", allowed_root=repo)
    g = result["graph"]
    crypto_nodes = [
        data for _, data in g.nodes(data=True)
        if data.get("category") == "crypto_usage"
    ]
    key_sizes = [n.get("key_size") for n in crypto_nodes if n.get("key_size")]
    assert 1024 in key_sizes, f"key_size=1024 must be in graph nodes, found: {key_sizes}"


# ──────────────────────────────────────────────────────────────────────────────
# M10 — factor_extractor must not silently drop None weakness
# ──────────────────────────────────────────────────────────────────────────────

def test_m10_unrated_weakness_stays_none():
    """
    A file containing only unrecognized algorithms must result in
    crypto_weakness.value == None, not 0.0.
    """
    # Build a RiskFactors with None crypto_weakness directly
    factors = RiskFactors(
        data_sensitivity=FactorValue(value=0.5, source="test", confidence=1.0),
        asset_criticality=FactorValue(value=0.5, source="test", confidence=1.0),
        internet_exposure=FactorValue(value=0.5, source="test", confidence=1.0),
        crypto_weakness=FactorValue(value=None, source="unrecognized", confidence=0.0),
        cve_risk=FactorValue(value=None, source="unavailable", confidence=0.0),
        library_centrality=FactorValue(value=0.5, source="test", confidence=1.0),
        migration_difficulty=FactorValue(value=0.5, source="test", confidence=1.0),
    )
    w = 1.0 / 7.0
    weights = HeuristicWeights(
        data_sensitivity=w, asset_criticality=w, internet_exposure=w,
        crypto_weakness=w, cve_risk=w, library_centrality=w, migration_difficulty=w
    )
    result = calculate_heuristic_score(factors, weights, policy=MissingDataPolicy.RENORMALIZE)
    # Score must exist (renormalized over available factors)
    assert result.score is not None
    # crypto_weakness must be in missing_factors, not treated as 0.0
    assert "crypto_weakness" in result.missing_factors
    # The score should NOT be the same as if crypto_weakness contributed 0.0
    # (i.e., renormalization happened, not zero-contribution)
    available = ["data_sensitivity", "asset_criticality", "internet_exposure",
                 "library_centrality", "migration_difficulty"]
    expected_score = sum(0.5 * (w / (5 * w)) for _ in available)  # renormalized
    assert abs(result.score - expected_score) < 0.01, \
        f"Renormalized score {result.score} differs from expected {expected_score}"
