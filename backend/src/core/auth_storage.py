import os
import uuid
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from contextlib import contextmanager
from src.core.auth import User
from src.core.storage import DEFAULT_STORAGE_DIR

# Whitelist of public research benchmark datasets and shared demo projects
# These datasets are read-accessible to authenticated researchers as shared reference artifacts,
# but cannot be mutated or overwritten by users, and are never silently claimed.
LEGACY_BENCHMARK_PROJECTS = frozenset({
    "python_cryptography",
    "python_bcrypt",
    "python_itsdangerous",
    "java_jjwt",
    "java_java_jwt",
    "go_crypto",
    "go_jwt",
    "go_jwt_go",
    "agile",
    "audit_test_project",
    "demo-project",
    "demo_project",
    "test_proj",
    "test_proj_2",
    "test_proj_scan_compat",
    "test_verification_scan",
    "test_proj_quotes",
    "export_test_project",
    "e2e-smoke-test-project",
})

class SQLiteAuthStorage:
    """
    SQLite persistence for user registration, authentication, project ownership,
    and token revocation. Conforms to the project's SQLite pattern.
    """
    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            db_path = os.environ.get("AGILEGRAPH_AUTH_DB")
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
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_projects (
                    project_id TEXT NOT NULL,
                    owner_username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, owner_username)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invalidated_tokens (
                    token TEXT PRIMARY KEY,
                    invalidated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_projects_proj ON user_projects(project_id)
            """)
            conn.commit()

    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Register a new user in SQLite."""
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username.strip().lower(), email.strip().lower(), password_hash, created_at)
            )
            conn.commit()
        return User(id=user_id, username=username.strip().lower(), email=email.strip().lower(), created_at=created_at)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Lookup a user by username."""
        clean_user = username.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, email, created_at FROM users WHERE username = ?",
                (clean_user,)
            ).fetchone()
            if not row:
                return None
            return User(id=row["id"], username=row["username"], email=row["email"], created_at=str(row["created_at"]))

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Lookup a user by email address."""
        clean_email = email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, email, created_at FROM users WHERE email = ?",
                (clean_email,)
            ).fetchone()
            if not row:
                return None
            return User(id=row["id"], username=row["username"], email=row["email"], created_at=str(row["created_at"]))

    def get_user_password_hash(self, username_or_email: str) -> Optional[str]:
        """Retrieve the bcrypt password hash for credentials verification."""
        clean_ident = username_or_email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = ? OR email = ?",
                (clean_ident, clean_ident)
            ).fetchone()
            if not row:
                return None
            return row["password_hash"]

    def assign_project_owner(self, project_id: str, username: str):
        """Record project ownership for data isolation."""
        clean_user = username.strip().lower()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_projects (project_id, owner_username) VALUES (?, ?)",
                (project_id.strip(), clean_user)
            )
            conn.commit()

    def get_project_owner(self, project_id: str) -> Optional[str]:
        """Find the owner of a given project_id."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT owner_username FROM user_projects WHERE project_id = ?",
                (project_id.strip(),)
            ).fetchone()
            if row:
                return row["owner_username"]
            return None

    def delete_project_owner(self, project_id: str):
        """Remove ownership mapping for a deleted project."""
        clean_proj = project_id.strip()
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM user_projects WHERE project_id = ?",
                (clean_proj,)
            )
            conn.commit()

    def check_user_owns_project(self, project_id: str, username: str, write: bool = False) -> bool:
        """
        Check if the requesting user has authorized access to the project.
        
        SAFE MULTI-USER ISOLATION POLICY:
        1. Explicit Owner:
           - If project_id has a recorded owner in user_projects, only that user is allowed.
        2. Known Shared Reference / Benchmark Projects:
           - If project_id is in LEGACY_BENCHMARK_PROJECTS (including 'agile' and the 8 benchmarks):
             * Read-only access (write=False) is granted to authenticated researchers.
               Ownership is never silently assigned.
             * Write/mutation access (write=True) is denied in production/authenticated mode
               to prevent modifying public benchmark datasets. (Allowed only in test mode).
        3. Unknown / Ownerless Projects:
           - If project_id has no owner and is not in LEGACY_BENCHMARK_PROJECTS:
             * ACCESS IS STRICTLY DENIED (returns False).
             * Unknown/ownerless projects are NEVER automatically accessible.
        """
        clean_user = username.strip().lower()
        clean_proj = project_id.strip()
        
        from src.core.auth import is_anonymous_allowed
        if is_anonymous_allowed() and clean_user == "anonymous_test_user":
            return True

        owner = self.get_project_owner(clean_proj)
        
        if owner is not None:
            return owner == clean_user
            
        # Project has no explicit owner in user_projects
        if clean_proj in LEGACY_BENCHMARK_PROJECTS:
            if write:
                from src.core.auth import is_anonymous_allowed
                return is_anonymous_allowed()
            return True
            
        # Unknown or ownerless project: strictly deny access
        return False

    def invalidate_token(self, token: str):
        """Add a token to the revoked tokens list."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO invalidated_tokens (token, invalidated_at) VALUES (?, ?)",
                (token, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()

    def is_token_invalidated(self, token: str) -> bool:
        """Check whether a token has been revoked."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM invalidated_tokens WHERE token = ?",
                (token,)
            )
            row_data = row.fetchone()
            return row_data is not None

# Default singleton instance
default_auth_storage = SQLiteAuthStorage()
