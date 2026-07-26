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
            # 4. Credentials Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_credentials (
                    client_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
            """)
            # 5. Integrations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_integrations (
                    id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    integration_name TEXT NOT NULL,
                    integration_type TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    encrypted_credential TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    last_tested_at INTEGER,
                    last_test_status TEXT NOT NULL DEFAULT 'Not Configured'
                )
            """)
            # 6. Team Members Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    client_access TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL
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

            # Seed credentials for client_abc and client_xyz if empty
            import time
            now = int(time.time())
            cursor.execute("SELECT COUNT(*) FROM client_credentials")
            if cursor.fetchone()[0] == 0:
                from backend.app.core.security import get_password_hash
                cred_seeds = [
                    ("client_abc", get_password_hash("password_abc"), now),
                    ("client_xyz", get_password_hash("password_xyz"), now),
                ]
                for cred in cred_seeds:
                    cursor.execute("INSERT OR REPLACE INTO client_credentials VALUES (?, ?, ?)", cred)
                conn.commit()

            # Seed initial team members if empty
            cursor.execute("SELECT COUNT(*) FROM team_members")
            if cursor.fetchone()[0] == 0:
                team_seeds = [
                    ("tm_01", "admin@company.com", "Admin", '["client_abc", "client_xyz"]', "active", now),
                    ("tm_02", "member@company.com", "Member", '["client_abc"]', "active", now),
                ]
                for tm in team_seeds:
                    cursor.execute("INSERT OR REPLACE INTO team_members VALUES (?, ?, ?, ?, ?, ?)", tm)
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

    # --- Client Integrations ---
    def create_integration(
        self,
        integration_id: str,
        client_id: str,
        integration_name: str,
        integration_type: str,
        endpoint_url: str,
        encrypted_credential: str,
        created_at: int
    ) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO client_integrations 
                (id, client_id, integration_name, integration_type, endpoint_url, encrypted_credential, created_at, last_tested_at, last_test_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'Not Configured')
                """,
                (integration_id, client_id, integration_name, integration_type, endpoint_url, encrypted_credential, created_at)
            )
            conn.commit()
            conn.close()
            return self.get_integration_by_id(integration_id, client_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create client integration: {str(e)}")

    def get_integrations(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, client_id, integration_name, integration_type, endpoint_url, encrypted_credential, created_at, last_tested_at, last_test_status FROM client_integrations WHERE client_id = ? ORDER BY created_at DESC",
                (client_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch client integrations: {str(e)}")

    def get_integration_by_id(self, integration_id: str, client_id: str) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, client_id, integration_name, integration_type, endpoint_url, encrypted_credential, created_at, last_tested_at, last_test_status FROM client_integrations WHERE id = ? AND client_id = ?",
                (integration_id, client_id)
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch integration record: {str(e)}")

    def update_integration_test_status(self, integration_id: str, client_id: str, status: str, tested_at: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE client_integrations SET last_test_status = ?, last_tested_at = ? WHERE id = ? AND client_id = ?",
                (status, tested_at, integration_id, client_id)
            )
            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()
            return updated
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update integration test status: {str(e)}")

    def delete_integration(self, integration_id: str, client_id: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM client_integrations WHERE id = ? AND client_id = ?",
                (integration_id, client_id)
            )
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete integration record: {str(e)}")

    # --- Team Members ---
    def get_team_members(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, role, client_access, status, created_at FROM team_members ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            import json
            result = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("client_access"), str):
                    try:
                        item["client_access"] = json.loads(item["client_access"])
                    except Exception:
                        item["client_access"] = [item["client_access"]]
                result.append(item)
            return result
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch team members: {str(e)}")

    def get_team_member_by_email(self, email: str) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, role, client_access, status, created_at FROM team_members WHERE LOWER(email) = LOWER(?)",
                (email,)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            item = dict(row)
            import json
            if isinstance(item.get("client_access"), str):
                try:
                    item["client_access"] = json.loads(item["client_access"])
                except Exception:
                    item["client_access"] = [item["client_access"]]
            return item
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch team member by email: {str(e)}")

    def get_team_member_by_id(self, member_id: str) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, role, client_access, status, created_at FROM team_members WHERE id = ?",
                (member_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            item = dict(row)
            import json
            if isinstance(item.get("client_access"), str):
                try:
                    item["client_access"] = json.loads(item["client_access"])
                except Exception:
                    item["client_access"] = [item["client_access"]]
            return item
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to fetch team member by id: {str(e)}")

    def create_team_member(
        self,
        member_id: str,
        email: str,
        role: str,
        client_access: List[str],
        status: str,
        created_at: int
    ) -> Dict[str, Any]:
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO team_members (id, email, role, client_access, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (member_id, email, role, json.dumps(client_access), status, created_at)
            )
            conn.commit()
            conn.close()
            return self.get_team_member_by_id(member_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create team member: {str(e)}")

    def update_team_member(self, member_id: str, role: str, client_access: List[str]) -> Dict[str, Any]:
        try:
            import json
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE team_members SET role = ?, client_access = ? WHERE id = ?",
                (role, json.dumps(client_access), member_id)
            )
            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()
            if not updated:
                return None
            return self.get_team_member_by_id(member_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update team member: {str(e)}")

    def delete_team_member(self, member_id: str) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete team member: {str(e)}")


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

