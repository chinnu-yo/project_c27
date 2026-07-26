import os
import sqlite3
import yaml
from typing import Dict, Any, List
from backend.app.core.exceptions import DatabaseError, ValidationError, SecurityError

DB_PATH = "client_vault.db"
TOOLS_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "mcp", "tools.yaml"
)


class SQLiteService:
    def __init__(self, db_path: str = DB_PATH, yaml_path: str = TOOLS_YAML_PATH):
        self.db_path = db_path
        self.yaml_path = yaml_path
        self._allowed_queries = self._load_tools_yaml()
        self.init_db()

    def _load_tools_yaml(self) -> Dict[str, Any]:
        """Loads allowed queries mapping from tools.yaml configuration."""
        if not os.path.exists(self.yaml_path):
            return {"allowed_queries": {}}
        try:
            with open(self.yaml_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("allowed_queries", {})
        except Exception as e:
            raise DatabaseError(f"Failed to load tools.yaml: {str(e)}")

    def init_db(self):
        """Creates standard tables and feeds sandbox seed records."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Projects Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_projects (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    budget REAL NOT NULL,
                    start_date TEXT DEFAULT '2026-01-15',
                    end_date TEXT DEFAULT '2026-12-31',
                    team_members TEXT DEFAULT 'Alice Miller, Sarah Connor'
                )
            """)

            # Migration check: add columns if table existed without them
            cursor.execute("PRAGMA table_info(client_projects)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            if "start_date" not in existing_cols:
                cursor.execute("ALTER TABLE client_projects ADD COLUMN start_date TEXT DEFAULT '2026-01-15'")
            if "end_date" not in existing_cols:
                cursor.execute("ALTER TABLE client_projects ADD COLUMN end_date TEXT DEFAULT '2026-12-31'")
            if "team_members" not in existing_cols:
                cursor.execute("ALTER TABLE client_projects ADD COLUMN team_members TEXT DEFAULT 'Alice Miller, Sarah Connor'")

            # 2. Contacts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_contacts (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    contact_name TEXT NOT NULL,
                    contact_email TEXT NOT NULL
                )
            """)
            # 3. Feedback Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_feedback (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    feedback_text TEXT NOT NULL,
                    received_at INTEGER NOT NULL
                )
            """)
            # 4. Credentials Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_credentials (
                    client_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
            """)
            conn.commit()

            # Seed sandbox data for client_abc and client_xyz
            seed_projects = [
                ("proj_01", "client_abc", "Q3 Brand Audit Campaign", "Active", 12000.00, "2026-06-01", "2026-09-30", "Alice Miller, Sarah Connor"),
                ("proj_02", "client_abc", "SEO Landing Page Suite", "Completed", 4500.00, "2026-03-01", "2026-05-31", "Bob Ross, Alice Miller"),
                ("proj_03", "client_abc", "Data Pipeline Overhaul", "Active", 22500.00, "2026-07-01", "2026-11-30", "DevOps Architect, Sarah Connor"),
                ("proj_04", "client_xyz", "Financial Dashboard Build", "Active", 25000.00, "2026-05-15", "2026-10-15", "John Doe, Alice Miller"),
                ("proj_05", "client_xyz", "Data Pipeline Overhaul", "Active", 18500.00, "2026-06-15", "2026-12-01", "John Doe, Sarah Connor"),
            ]
            for proj in seed_projects:
                cursor.execute("INSERT OR REPLACE INTO client_projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)", proj)

            seed_contacts = [
                ("cont_01", "client_abc", "Alice Miller", "alice@abc.com"),
                ("cont_02", "client_xyz", "John Doe", "john@xyz.com"),
                ("cont_03", "client_abc", "Sarah Connor", "sarah@abc.com"),
            ]
            for cont in seed_contacts:
                cursor.execute("INSERT OR REPLACE INTO client_contacts VALUES (?, ?, ?, ?)", cont)

            seed_feedback = [
                ("feed_01", "client_abc", "Always use the clean financial layout template for client_abc corporate reporting.", 1774845000),
            ]
            for feed in seed_feedback:
                cursor.execute("INSERT OR REPLACE INTO client_feedback VALUES (?, ?, ?, ?)", feed)
            conn.commit()

            # Seed credentials for client_abc and client_xyz if empty
            cursor.execute("SELECT COUNT(*) FROM client_credentials")
            if cursor.fetchone()[0] == 0:
                import time
                from backend.app.core.security import get_password_hash
                now = int(time.time())
                cred_seeds = [
                    ("client_abc", get_password_hash("password_abc"), now),
                    ("client_xyz", get_password_hash("password_xyz"), now),
                ]
                for cred in cred_seeds:
                    cursor.execute("INSERT OR REPLACE INTO client_credentials VALUES (?, ?, ?)", cred)
                conn.commit()

            conn.close()
        except Exception as e:
            raise DatabaseError(f"SQLite DB initialization failed: {str(e)}")

    def get_client_credentials(self, client_id: str) -> Dict[str, Any]:
        """Retrieves stored credentials for a given client_id."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT client_id, password_hash, created_at FROM client_credentials WHERE client_id = ?",
                (client_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch client credentials: {str(e)}")


    def run_query(self, query_name: str, params: Dict[str, Any], client_id: str) -> List[Dict[str, Any]]:
        """Executes a mapped read-only query safely with strict tenant isolation."""
        if query_name not in self._allowed_queries:
            raise ValidationError(f"Query '{query_name}' is not allowed or does not exist.")

        query_config = self._allowed_queries[query_name]
        sql_template = query_config["sql"]

        # Enforce multi-tenancy validation parameters
        params["client_id"] = client_id

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql_template, params)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Database query execution failure: {str(e)}")
        except Exception as e:
            raise SecurityError(f"Query authorization error: {str(e)}")
