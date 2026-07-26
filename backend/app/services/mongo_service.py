import time
from pymongo import MongoClient
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings

class MongoService:
    def __init__(self, uri: str = settings.mongodb_uri):
        self._in_memory_templates: Dict[str, Dict[str, Any]] = {}
        try:
            # Short timeout to detect connection issues immediately during startup
            self.client = MongoClient(uri, serverSelectionTimeoutMS=1500)
            self.client.admin.command('ping')
            self.db = self.client.get_database("agentic_workspace")
            self._ensure_indexes()
            self._seed_crm_records()
        except Exception:
            # Clean fallback settings if Mongo server is unreachable
            self.client = None
            self.db = None

    def _ensure_indexes(self):
        """Indexes key search paths to speed up database queries."""
        if self.db is not None:
            try:
                self.db.report_templates.create_index("client_id")
                self.db.report_templates.create_index("template_id", unique=True)
                self.db.dashboard_notifications.create_index("client_id")
                self.db.reports.create_index("client_id")
                self.db.crm_records.create_index("client_id")
            except Exception:
                pass

    def _seed_crm_records(self):
        """Seeds initial CRM notes and contract records if crm_records collection is empty."""
        if self.db is not None:
            try:
                count = self.db.crm_records.count_documents({"client_id": "client_abc"})
                if count == 0:
                    seed_docs = [
                        {
                            "client_id": "client_abc",
                            "record_type": "crm_note",
                            "title": "Q3 Layout Preference Alignment",
                            "content": "Client client_abc requested Q3 custom financial layout and dark mode theme alignment.",
                            "author": "Alice Miller",
                            "created_at": 1774845000
                        },
                        {
                            "client_id": "client_abc",
                            "record_type": "contract",
                            "title": "Enterprise Service Level Agreement",
                            "content": "Contract #CT-2026-ABC signed for $50,000/yr enterprise support, autorenewal Oct 2026.",
                            "author": "Legal Vault",
                            "created_at": 1774845100
                        },
                        {
                            "client_id": "client_abc",
                            "record_type": "crm_note",
                            "title": "Quarterly Executive Review Meeting",
                            "content": "Quarterly executive review meeting scheduled with account manager Alice Miller.",
                            "author": "Sarah Connor",
                            "created_at": 1774845200
                        }
                    ]
                    self.db.crm_records.insert_many(seed_docs)
            except Exception:
                pass

    def search_records(self, client_id: str, query: str = "") -> List[Dict[str, Any]]:
        """Queries CRM notes and contract records for client_id, returning fallback seed data if MongoDB is offline."""
        if self.db is not None:
            try:
                q_dict: Dict[str, Any] = {"client_id": client_id}
                if query:
                    q_dict["$or"] = [
                        {"content": {"$regex": query, "$options": "i"}},
                        {"title": {"$regex": query, "$options": "i"}},
                        {"record_type": {"$regex": query, "$options": "i"}}
                    ]
                records = list(self.db.crm_records.find(q_dict))
                if records:
                    return [{**item, "_id": str(item["_id"])} for item in records]
            except Exception:
                pass

        # Fallback offline seed array
        fallback_seeds = [
            {
                "_id": "rec_001",
                "client_id": client_id,
                "record_type": "crm_note",
                "title": "Q3 Layout Preference Alignment",
                "content": f"Client {client_id} requested Q3 custom financial layout and dark mode theme alignment.",
                "author": "Alice Miller"
            },
            {
                "_id": "rec_002",
                "client_id": client_id,
                "record_type": "contract",
                "title": "Enterprise Service Level Agreement",
                "content": f"Contract #CT-2026-{client_id.upper()} signed for $50,000/yr enterprise support, autorenewal Oct 2026.",
                "author": "Legal Vault"
            },
            {
                "_id": "rec_003",
                "client_id": client_id,
                "record_type": "crm_note",
                "title": "Quarterly Executive Review Meeting",
                "content": f"Quarterly executive review meeting scheduled for {client_id} with account manager Alice Miller.",
                "author": "Sarah Connor"
            }
        ]

        if not query:
            return fallback_seeds

        q_lower = query.lower()
        filtered = [
            rec for rec in fallback_seeds
            if q_lower in rec["title"].lower() or q_lower in rec["content"].lower() or q_lower in rec["record_type"].lower()
        ]
        return filtered if filtered else fallback_seeds

    def get_template(self, client_id: str) -> Dict[str, Any]:
        """Loads a blueprint layout template, falling back gracefully to defaults on network error."""
        if self.db is not None:
            try:
                res = self.db.report_templates.find_one({"client_id": client_id})
                if res:
                    return res
            except Exception:
                pass
        
        # Check in-memory stored templates if any exist for client
        for t in self._in_memory_templates.values():
            if t.get("client_id") == client_id:
                return t

        return self._get_fallback_template(client_id)

    def get_template_by_id(self, template_id: str, client_id: str) -> Dict[str, Any]:
        """
        Fetches a specific template by template_id for client_id.
        Raises KeyError/ValueError if missing or client mismatch — does NOT silently fall back.
        """
        res = None
        if self.db is not None:
            try:
                res = self.db.report_templates.find_one({"template_id": template_id})
            except Exception:
                pass

        if res is None:
            res = self._in_memory_templates.get(template_id)

        if not res:
            raise KeyError(f"Template with ID '{template_id}' not found.")

        if res.get("client_id") != client_id:
            raise ValueError(f"Template '{template_id}' does not belong to client '{client_id}'.")

        return res

    def save_template(self, doc: Dict[str, Any]) -> str:
        """Stores template metadata and parsed structure in database and memory cache."""
        template_id = doc.get("template_id")
        self._in_memory_templates[template_id] = doc
        if self.db is not None:
            try:
                self.db.report_templates.insert_one(doc)
            except Exception:
                pass
        return template_id

    def list_templates(self, client_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of all templates for a client_id."""
        templates_dict: Dict[str, Dict[str, Any]] = {}
        
        if self.db is not None:
            try:
                cursor = self.db.report_templates.find({"client_id": client_id})
                for item in cursor:
                    item_copy = {**item}
                    if "_id" in item_copy:
                        item_copy["_id"] = str(item_copy["_id"])
                    t_id = item_copy.get("template_id")
                    if t_id:
                        templates_dict[t_id] = item_copy
            except Exception:
                pass

        # Include in-memory templates
        for t_id, item in self._in_memory_templates.items():
            if item.get("client_id") == client_id:
                templates_dict[t_id] = item

        return list(templates_dict.values())

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
        template_text = (
            "1. Executive Financial Summary\n"
            "2. Invoicing & Payment Breakdown\n"
            "3. CRM Pipeline\n"
            "4. Financial Recommendations"
        )
        return {
            "client_id": client_id,
            "template_name": "Executive Corporate Report",
            "extracted_structure": {
                "template_text_content": template_text,
                "raw_text_layout": template_text
            },
            "tiptap_schema_blueprint": {
                "type": "doc",
                "content": [
                    { "type": "heading", "attrs": { "level": 1 }, "content": [{ "type": "text", "text": "Executive Financial Summary" }] },
                    { "type": "paragraph", "content": [{ "type": "text", "text": "Overview of financial operations and performance." }] },
                    { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "Invoicing & Payment Breakdown" }] },
                    { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "CRM Pipeline" }] },
                    { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "Financial Recommendations" }] }
                ]
            }
        }
