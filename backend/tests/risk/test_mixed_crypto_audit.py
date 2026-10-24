import pytest
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.risk.factor_extractor import FactorExtractor


def test_strong_known_crypto_alone():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_sha256", category="file"))
    ag.add_node(GraphNode(id="cu_sha256", category="crypto_usage", properties={"algorithm": "sha256"}))
    ag.add_edge(GraphEdge(source_id="file_sha256", target_id="cu_sha256", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_sha256", {}, {}, {})

    assert factors.crypto_weakness.value == 0.1
    assert factors.crypto_weakness.confidence == 0.9
    assert "algorithm classification (sha256)" in factors.crypto_weakness.source


def test_weak_known_crypto_alone():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_md5", category="file"))
    ag.add_node(GraphNode(id="cu_md5", category="crypto_usage", properties={"algorithm": "md5"}))
    ag.add_edge(GraphEdge(source_id="file_md5", target_id="cu_md5", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_md5", {}, {}, {})

    assert factors.crypto_weakness.value == 1.0
    assert factors.crypto_weakness.confidence == 0.9
    assert "algorithm classification (md5)" in factors.crypto_weakness.source


def test_unknown_crypto_alone():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_unknown", category="file"))
    ag.add_node(GraphNode(id="cu_unknown", category="crypto_usage", properties={"algorithm": "vigenere_stream_custom"}))
    ag.add_edge(GraphEdge(source_id="file_unknown", target_id="cu_unknown", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_unknown", {}, {}, {})

    # Unknown alone must be None, NOT 0.0 (not safe)
    assert factors.crypto_weakness.value is None
    assert factors.crypto_weakness.confidence == 0.0
    assert "vigenere_stream_custom" in factors.crypto_weakness.source


def test_mixed_strong_known_and_unknown_crypto():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_mixed", category="file"))
    ag.add_node(GraphNode(id="cu_strong", category="crypto_usage", properties={"algorithm": "sha256"}))
    ag.add_node(GraphNode(id="cu_unrated", category="crypto_usage", properties={"algorithm": "obscure_cipher_z"}))
    ag.add_edge(GraphEdge(source_id="file_mixed", target_id="cu_strong", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file_mixed", target_id="cu_unrated", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_mixed", {}, {}, {})

    # Active Policy (Evidence-preserving with uncertainty discount):
    # - Value takes recognized risk (0.1)
    # - Epistemic uncertainty discounts confidence from 0.90 to 0.65
    # - Audit trail preserves unrated cipher name for human review
    assert factors.crypto_weakness.value == 0.1
    assert factors.crypto_weakness.confidence == 0.65
    assert "obscure_cipher_z" in factors.crypto_weakness.source
    assert "unrated crypto also detected" in factors.crypto_weakness.source


def test_mixed_weak_known_and_unknown_crypto():
    ag = AgileGraph()
    ag.add_node(GraphNode(id="file_mixed_weak", category="file"))
    ag.add_node(GraphNode(id="cu_weak", category="crypto_usage", properties={"algorithm": "des"}))
    ag.add_node(GraphNode(id="cu_unrated", category="crypto_usage", properties={"algorithm": "obscure_cipher_z"}))
    ag.add_edge(GraphEdge(source_id="file_mixed_weak", target_id="cu_weak", relationship="CONTAINS"))
    ag.add_edge(GraphEdge(source_id="file_mixed_weak", target_id="cu_unrated", relationship="CONTAINS"))

    extractor = FactorExtractor(ag)
    factors = extractor.extract("file_mixed_weak", {}, {}, {})

    assert factors.crypto_weakness.value == 1.0
    assert factors.crypto_weakness.confidence == 0.65
    assert "obscure_cipher_z" in factors.crypto_weakness.source
