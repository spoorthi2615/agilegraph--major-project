import os
import json
import pytest
import tempfile
import networkx as nx
from src.core.storage import ProjectStorage, SQLiteMigrationStorage, sanitize_project_id
from src.models.migration_state import MigrationStateRecord, MigrationLifecycleState

def test_sanitize_project_id():
    assert sanitize_project_id("valid_project_1") == "valid_project_1"
    assert sanitize_project_id("org-repo.sub") == "org-repo.sub"

    with pytest.raises(ValueError, match="Path traversal"):
        sanitize_project_id("../evil")

    with pytest.raises(ValueError, match="Path traversal"):
        sanitize_project_id("evil/path")

    with pytest.raises(ValueError, match="invalid characters"):
        sanitize_project_id("project*bad!chars")

def test_project_storage_roundtrip_graph_and_scores():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ProjectStorage(base_dir=tmpdir)

        g = nx.MultiDiGraph()
        g.add_node("node1", category="file", language="PYTHON", lines=42)
        g.add_node("node2", category="crypto_usage", algorithm="aes")
        g.add_edge("node1", "node2", relationship="CONTAINS_USAGE")

        scores = [
            {"asset_id": "node1", "score": 0.75, "missing_factors": ["cve_risk"]}
        ]
        prov = {"scanned_files": 1}

        scan_data = {
            "graph": g,
            "scores": scores,
            "provenance": prov
        }

        storage.save_scan_result("proj_alpha", scan_data)

        loaded = storage.load_scan_result("proj_alpha")
        assert loaded is not None
        assert loaded["scores"] == scores
        assert loaded["provenance"] == prov

        g_loaded = loaded["graph"]
        assert isinstance(g_loaded, nx.MultiDiGraph)
        assert len(g_loaded.nodes) == 2
        assert len(g_loaded.edges) == 1
        assert g_loaded.nodes["node1"]["category"] == "file"
        assert g_loaded.nodes["node1"]["language"] == "PYTHON"
        assert g_loaded.nodes["node1"]["lines"] == 42
        assert g_loaded.nodes["node2"]["algorithm"] == "aes"

def test_sqlite_migration_storage_tables_and_transitions():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_migrations.db")
        sqlite_storage = SQLiteMigrationStorage(db_path=db_path)

        # 1. Record project
        sqlite_storage.record_project("proj1", {"author": "AgileGraph"})

        # 2. Record initial transition
        rec1 = sqlite_storage.record_transition(
            project_id="proj1",
            asset_id="asset:main.py",
            to_state=MigrationLifecycleState.EVALUATED,
            reason="Initial risk assessment completed",
            operator="automated_pipeline"
        )
        assert rec1.current_state == MigrationLifecycleState.EVALUATED
        assert rec1.previous_state == MigrationLifecycleState.DISCOVERED

        # 3. Record next transition
        rec2 = sqlite_storage.record_transition(
            project_id="proj1",
            asset_id="asset:main.py",
            to_state=MigrationLifecycleState.IN_PLANNING,
            reason="Selected for Post-Quantum Migration",
            operator="security_lead"
        )
        assert rec2.current_state == MigrationLifecycleState.IN_PLANNING
        assert rec2.previous_state == MigrationLifecycleState.EVALUATED

        # 4. Read back current state
        state = sqlite_storage.get_state("proj1", "asset:main.py")
        assert state is not None
        assert state.current_state == MigrationLifecycleState.IN_PLANNING

        # 5. Read transition history (audit trail)
        history = sqlite_storage.get_transition_history("proj1", "asset:main.py")
        assert len(history) == 2
        assert history[0]["from_state"] == "DISCOVERED"
        assert history[0]["to_state"] == "EVALUATED"
        assert history[0]["reason"] == "Initial risk assessment completed"
        assert history[1]["from_state"] == "EVALUATED"
        assert history[1]["to_state"] == "IN_PLANNING"

def test_project_storage_roadmap_state_persistence_dual_sync():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ProjectStorage(base_dir=tmpdir)

        records = {
            "asset1": MigrationStateRecord(
                asset_id="asset1",
                current_state=MigrationLifecycleState.EVALUATED,
                previous_state=MigrationLifecycleState.DISCOVERED
            ),
            "asset2": MigrationStateRecord(
                asset_id="asset2",
                current_state=MigrationLifecycleState.IN_PLANNING,
                previous_state=MigrationLifecycleState.EVALUATED
            )
        }

        storage.save_roadmap_state("roadmap_proj", records)

        loaded_map = storage.load_roadmap_state("roadmap_proj")
        assert len(loaded_map) == 2
        assert loaded_map["asset1"]["current_state"] == "EVALUATED"
        assert loaded_map["asset1"]["previous_state"] == "DISCOVERED"
        assert loaded_map["asset2"]["current_state"] == "IN_PLANNING"

def test_project_storage_malformed_file_handling():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ProjectStorage(base_dir=tmpdir)
        proj_dir = os.path.join(tmpdir, "corrupt_proj")
        os.makedirs(proj_dir, exist_ok=True)

        with open(os.path.join(proj_dir, "scan_result.json"), "w") as f:
            f.write("NOT_A_VALID_JSON{[[")

        assert storage.load_scan_result("corrupt_proj") is None
