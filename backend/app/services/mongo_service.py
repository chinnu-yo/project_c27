import time
from pymongo import MongoClient
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

class MongoService:
    def __init__(self, uri: str = settings.mongodb_uri):
        try:
            # Short timeout to detect connection issues immediately during startup
            self.client = MongoClient(uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command('ping')
            self.db = self.client.get_database("agentic_workspace")
            self._ensure_indexes()
        except Exception:
            # Clean fallback settings if Mongo server is unreachable
            self.client = None
            self.db = None

    def _ensure_indexes(self):
        """Indexes key search paths to speed up database queries."""
        if self.db is not None:
            try:
                self.db.report_templates.create_index("client_id")
                self.db.dashboard_notifications.create_index("client_id")
                self.db.reports.create_index("client_id")
            except Exception:
                pass

    def get_template(self, client_id: str) -> Dict[str, Any]:
        """Loads a blueprint layout template, falling back gracefully to defaults on network error."""
        if self.db is not None:
            try:
                res = self.db.report_templates.find_one({"client_id": client_id})
                if res:
                    return res
            except Exception:
                pass
        return self._get_fallback_template(client_id)

    def save_report(self, client_id: str, report_name: str, tiptap_json: dict) -> str:
        """Stores report canvas structure, returning a simulated ID if saving fails."""
        if self.db is not None:
            try:
                doc = {
                    "client_id": client_id,
                    "report_name": report_name,
                    "tiptap_json": tiptap_json,
                    "saved_at": int(time.time())
                }
                res = self.db.reports.insert_one(doc)
                return str(res.inserted_id)
            except Exception:
                pass
        return "simulated_report_id_101"

    def insert_notification(self, doc: Dict[str, Any]):
        """Inserts validation preferences cards, discarding silently on connection failure."""
        if self.db is not None:
            try:
                self.db.dashboard_notifications.insert_one(doc)
            except Exception:
                pass

    def update_notification(self, notification_id: str, client_id: str, status: str):
        """Updates the status of a specific dashboard notification, enforcing tenant constraints."""
        if self.db is not None:
            try:
                self.db.dashboard_notifications.update_one(
                    {"_id": notification_id, "client_id": client_id},
                    {"$set": {"status": status}}
                )
            except Exception:
                pass

    def get_pending_notifications(self, client_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of pending validations, returning sandbox seeds if offline."""
        if self.db is not None:
            try:
                res = self.db.dashboard_notifications.find(
                    {"client_id": client_id, "status": "pending_approval"}
                )
                return [{**item, "_id": str(item["_id"])} for item in res]
            except Exception:
                pass
        return self._get_fallback_notifications(client_id)

    def _get_fallback_notifications(self, client_id: str) -> List[Dict[str, Any]]:
        """Static mockup array representing pending supervisor fact verification notifications."""
        return [
            {
                "_id": "notif_99b12d45",
                "client_id": client_id,
                "status": "pending_approval",
                "message": f"I noticed you corrected the Q3 report format for {client_id}. Remember this rule?",
                "extracted_fact": f"Always use the clean financial layout template for {client_id} corporate reporting.",
                "domain": "formatting_preference",
                "created_at": 1774845000
            }
        ]

    def _get_fallback_template(self, client_id: str) -> Dict[str, Any]:
        """Static layout schema for offline sandbox testing environments."""
        return {
            "client_id": client_id,
            "template_name": "Executive Quarterly Report",
            "tiptap_schema_blueprint": {
                "type": "doc",
                "content": [
                    { "type": "heading", "attrs": { "level": 1 }, "content": [{ "type": "text", "text": "Performance Review" }] },
                    { "type": "paragraph", "content": [{ "type": "text", "text": "Overview of operational metrics." }] }
                ]
            }
        }
