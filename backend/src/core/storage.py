import os
import json
import re
import sqlite3
import tempfile
import networkx as nx
from contextlib import contextmanager
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from src.core.logger import get_logger
from src.models.migration_state import (
    MigrationStateRecord,
    MigrationLifecycleState,
    transition_state,
    parse_lifecycle_state,
)

logger = get_logger(__name__)

# Default storage directory under backend/dataset/cache
DEFAULT_STORAGE_DIR = os.path.realpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dataset", "cache")
)

def sanitize_project_id(project_id: str) -> str:
    """
    Validates and sanitizes a project_id to prevent path traversal.
    Allows only alphanumeric characters, underscores, hyphens, and single dots.
    """
    if not project_id or not isinstance(project_id, str):
        raise ValueError("Invalid project_id: must be a non-empty string.")
    
    clean_id = project_id.strip()
    
    if ".." in clean_id or "/" in clean_id or "\\" in clean_id:
        raise ValueError(f"Path traversal detected in project_id: {project_id}")
        
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", clean_id):
        raise ValueError(f"project_id contains invalid characters: {project_id}")
        
    return clean_id


class SQLiteMigrationStorage:
    """
    SQLite persistence for project migration lifecycle states and append-only audit trail.
    Schema conforms to Synopsis Section 5.6:
      - projects: metadata and registration
      - migration_states: current lifecycle state per asset
      - migration_transitions: append-only transition audit log
    """
    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            env_db = os.environ.get("DATABASE_URL")
            if env_db and env_db.startswith("sqlite:///"):
                db_path = env_db.replace("sqlite:///", "")
            elif env_db and env_db.startswith("sqlite://"):
                db_path = env_db.replace("sqlite://", "")
        if not db_path:
            db_path = os.path.join(DEFAULT_STORAGE_DIR, "agilegraph_migrations.db")
        self.db_path = os.path.realpath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_states (
                    project_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    previous_state TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, asset_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    operator TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trans_proj_asset 
                ON migration_transitions(project_id, asset_id)
            """)
            conn.commit()

    def record_project(self, project_id: str, metadata: Optional[Dict[str, Any]] = None):
        safe_id = sanitize_project_id(project_id)
        meta_json = json.dumps(metadata or {})
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO projects (project_id, metadata) VALUES (?, ?)",
                (safe_id, meta_json)
            )
            conn.commit()

    def get_state(self, project_id: str, asset_id: str) -> Optional[MigrationStateRecord]:
        safe_id = sanitize_project_id(project_id)
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT asset_id, current_state, previous_state, updated_at FROM migration_states WHERE project_id = ? AND asset_id = ?",
                (safe_id, asset_id)
            ).fetchone()
            if not row:
                return None
            return MigrationStateRecord(
                asset_id=row["asset_id"],
                current_state=parse_lifecycle_state(row["current_state"]),
                previous_state=parse_lifecycle_state(row["previous_state"]) if row["previous_state"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if "T" in str(row["updated_at"]) else datetime.now(timezone.utc)
            )

    def get_all_states(self, project_id: str) -> Dict[str, MigrationStateRecord]:
        safe_id = sanitize_project_id(project_id)
        result = {}
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT asset_id, current_state, previous_state, updated_at FROM migration_states WHERE project_id = ?",
                (safe_id,)
            ).fetchall()
            for row in rows:
                result[row["asset_id"]] = MigrationStateRecord(
                    asset_id=row["asset_id"],
                    current_state=parse_lifecycle_state(row["current_state"]),
                    previous_state=parse_lifecycle_state(row["previous_state"]) if row["previous_state"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if "T" in str(row["updated_at"]) else datetime.now(timezone.utc)
                )
        return result

    def record_transition(
        self,
        project_id: str,
        asset_id: str,
        to_state: MigrationLifecycleState | str,
        reason: Optional[str] = None,
        operator: Optional[str] = None
    ) -> MigrationStateRecord:
        safe_id = sanitize_project_id(project_id)
        target_enum = parse_lifecycle_state(to_state)
        
        current_record = self.get_state(safe_id, asset_id)
        if not current_record:
            current_record = MigrationStateRecord(
                asset_id=asset_id,
                current_state=MigrationLifecycleState.DISCOVERED
            )

        new_record = transition_state(current_record, target_enum, reason=reason, operator=operator)
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO migration_states 
                (project_id, asset_id, current_state, previous_state, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    safe_id,
                    asset_id,
                    new_record.current_state.value,
                    new_record.previous_state.value if new_record.previous_state else None,
                    now_iso
                )
            )
            conn.execute(
                """
                INSERT INTO migration_transitions
                (project_id, asset_id, from_state, to_state, transitioned_at, reason, operator)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    safe_id,
                    asset_id,
                    current_record.current_state.value if current_record else None,
                    new_record.current_state.value,
                    now_iso,
                    reason,
                    operator
                )
            )
            conn.commit()

        return new_record

    def get_transition_history(self, project_id: str, asset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        safe_id = sanitize_project_id(project_id)
        with self._get_connection() as conn:
            if asset_id:
                rows = conn.execute(
                    """
                    SELECT id, project_id, asset_id, from_state, to_state, transitioned_at, reason, operator
                    FROM migration_transitions
                    WHERE project_id = ? AND asset_id = ?
                    ORDER BY id ASC
                    """,
                    (safe_id, asset_id)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, project_id, asset_id, from_state, to_state, transitioned_at, reason, operator
                    FROM migration_transitions
                    WHERE project_id = ?
                    ORDER BY id ASC
                    """,
                    (safe_id,)
                ).fetchall()
            return [dict(r) for r in rows]

    def delete_project_records(self, project_id: str):
        safe_id = sanitize_project_id(project_id)
        with self._get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE project_id = ?", (safe_id,))
            conn.execute("DELETE FROM migration_states WHERE project_id = ?", (safe_id,))
            conn.execute("DELETE FROM migration_transitions WHERE project_id = ?", (safe_id,))
            conn.commit()


class ProjectStorage:
    def __init__(self, base_dir: str = DEFAULT_STORAGE_DIR, db_path: Optional[str] = None):
        self.base_dir = os.path.realpath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        if not db_path:
            db_path = os.path.join(self.base_dir, "agilegraph_migrations.db")
        self.sqlite_storage = SQLiteMigrationStorage(db_path=db_path)

    def _get_project_dir(self, project_id: str) -> str:
        safe_id = sanitize_project_id(project_id)
        project_dir = os.path.join(self.base_dir, safe_id)
        if os.path.commonpath([self.base_dir, os.path.realpath(project_dir)]) != self.base_dir:
            raise ValueError(f"Resolved path escapes storage root: {project_id}")
        return project_dir

    def _atomic_write_json(self, target_path: str, data: Any):
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)
        
        temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="tmp_agilegraph_", suffix=".json")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, target_path)
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    def save_scan_result(self, project_id: str, scan_result: Dict[str, Any]):
        project_dir = self._get_project_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)

        graph_obj = scan_result.get("graph")
        if isinstance(graph_obj, (nx.Graph, nx.DiGraph, nx.MultiDiGraph)):
            graph_data = nx.node_link_data(graph_obj)
        else:
            graph_data = graph_obj

        scores_data = scan_result.get("scores", [])
        prov_data = scan_result.get("provenance", {})

        payload = {
            "project_id": project_id,
            "provenance": prov_data,
            "scores": scores_data,
            "graph": graph_data
        }

        target_file = os.path.join(project_dir, "scan_result.json")
        self._atomic_write_json(target_file, payload)
        self.sqlite_storage.record_project(project_id, {"scores_count": len(scores_data)})
        logger.info(f"Persisted scan result for project: {project_id}")

    def load_scan_result(self, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            project_dir = self._get_project_dir(project_id)
            target_file = os.path.join(project_dir, "scan_result.json")
            if not os.path.exists(target_file):
                return None

            with open(target_file, "r", encoding="utf-8") as f:
                payload = json.load(f)

            graph_data = payload.get("graph")
            if graph_data:
                graph_obj = nx.node_link_graph(graph_data, directed=True, multigraph=True)
            else:
                graph_obj = nx.MultiDiGraph()

            return {
                "graph": graph_obj,
                "scores": payload.get("scores", []),
                "provenance": payload.get("provenance", {})
            }
        except Exception as e:
            logger.warning(f"Failed to load scan result for {project_id}: {e}")
            return None

    def save_roadmap_state(self, project_id: str, roadmap_records: Dict[str, Any]):
        """
        Persists roadmap state records to both SQLite and atomic JSON for complete compatibility.
        """
        project_dir = self._get_project_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)

        serialized = {}
        for asset_id, rec in roadmap_records.items():
            if hasattr(rec, "model_dump"):
                record_dict = rec.model_dump(mode="json")
                serialized[asset_id] = record_dict
            elif isinstance(rec, dict):
                record_dict = rec
                serialized[asset_id] = rec
            else:
                record_dict = {"asset_id": asset_id, "current_state": str(rec)}
                serialized[asset_id] = str(rec)

            # Persist to SQLite
            c_state = record_dict.get("current_state", "DISCOVERED")
            p_state = record_dict.get("previous_state")
            try:
                c_enum = parse_lifecycle_state(c_state)
                p_enum = parse_lifecycle_state(p_state) if p_state else None
                with self.sqlite_storage._get_connection() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO migration_states 
                        (project_id, asset_id, current_state, previous_state, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (project_id, asset_id, c_enum.value, p_enum.value if p_enum else None, datetime.now(timezone.utc).isoformat())
                    )
                    conn.commit()
            except Exception as e:
                logger.debug(f"SQLite sync note: {e}")

        target_file = os.path.join(project_dir, "roadmap.json")
        self._atomic_write_json(target_file, serialized)
        logger.info(f"Persisted roadmap state for project: {project_id}")

    def load_roadmap_state(self, project_id: str) -> Dict[str, Any]:
        """
        Loads roadmap state records. Checks SQLite first, falls back to roadmap.json.
        """
        try:
            sqlite_states = self.sqlite_storage.get_all_states(project_id)
            if sqlite_states:
                return {aid: rec.model_dump(mode="json") for aid, rec in sqlite_states.items()}

            project_dir = self._get_project_dir(project_id)
            target_file = os.path.join(project_dir, "roadmap.json")
            if not os.path.exists(target_file):
                return {}

            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to load roadmap state for {project_id}: {e}")
            return {}

    def delete_project(self, project_id: str):
        try:
            self.sqlite_storage.delete_project_records(project_id)
            project_dir = self._get_project_dir(project_id)
            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir, ignore_errors=True)
                logger.info(f"Deleted storage for project: {project_id}")
        except Exception as e:
            logger.warning(f"Failed to delete project storage for {project_id}: {e}")

# Default singleton storage instance
default_storage = ProjectStorage()
