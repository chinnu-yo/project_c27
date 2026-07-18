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
                    budget REAL NOT NULL
                )
            """)
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
            conn.commit()

            # Seed sandbox data for client_abc and client_xyz if empty
            cursor.execute("SELECT COUNT(*) FROM client_projects")
            if cursor.fetchone()[0] == 0:
                seed_data = [
                    # projects
                    ("proj_01", "client_abc", "Q3 Brand Audit Campaign", "Active", 12000.00),
                    ("proj_02", "client_abc", "SEO Landing Page Suite", "Completed", 4500.00),
                    ("proj_03", "client_xyz", "Financial Dashboard Build", "Active", 25000.00),
                    # contacts
                    ("cont_01", "client_abc", "Alice Miller", "alice@abc.com"),
                    ("cont_02", "client_xyz", "John Doe", "john@xyz.com"),
                    # feedback
                    ("feed_01", "client_abc", "Always use the clean financial layout template for client_abc corporate reporting.", 1774845000),
                ]
                for item in seed_data:
                    if item[0].startswith("proj_"):
                        cursor.execute("INSERT OR REPLACE INTO client_projects VALUES (?, ?, ?, ?, ?)", item)
                    elif item[0].startswith("cont_"):
                        cursor.execute("INSERT OR REPLACE INTO client_contacts VALUES (?, ?, ?, ?)", item)
                    elif item[0].startswith("feed_"):
                        cursor.execute("INSERT OR REPLACE INTO client_feedback VALUES (?, ?, ?, ?)", item)
                conn.commit()
            conn.close()
        except Exception as e:
            raise DatabaseError(f"SQLite DB initialization failed: {str(e)}")

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
