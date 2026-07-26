import json
from typing import Optional
import google.generativeai as genai
from fastapi import BackgroundTasks
from backend.app.core.config import settings, get_effective_tenant_key
from backend.app.services.chroma_service import ChromaMemoryLayer
from backend.app.services.mongo_service import MongoService
from backend.app.services.local_tools import LocalToolsManager, get_ga4_metrics, get_quickbooks_data
from backend.app.mcp_mocks.hubspot_sse import get_hubspot_data
from backend.app.services.critic_service import CriticService

class OrchestrationEngine:
    def __init__(
        self,
        chroma_client: ChromaMemoryLayer,
        mongo_client: MongoService,
        local_tools: LocalToolsManager,
        critic_service: CriticService
    ):
        self.chroma = chroma_client
        self.mongo = mongo_client
        self.tools = local_tools
        self.critic = critic_service

    async def execute_workflow(
        self,
        client_id: str,
        raw_user_prompt: str,
        background_tasks: BackgroundTasks,
        template_id: Optional[str] = None
    ) -> dict:
        """Coordinates retrieval of constraints, calls generation suite with tenant API key overrides, and triggers background Critic review."""
        # Dynamic API key overrides for Gemini, Mongo, HubSpot
        effective_gemini_key = get_effective_tenant_key(client_id, "Gemini", self.tools.sqlite_service)
        if effective_gemini_key:
            genai.configure(api_key=effective_gemini_key)
        
        # Step 1: Query local vector space for semantic formatting rules
        historical_context = await self.chroma.retrieve_client_facts(
            client_id=client_id,
            query=raw_user_prompt
        )
        
        # Step 2: Grab layout template configurations
        if template_id:
            # Fetch specific template structure using get_template_by_id (raises error if invalid/tenant mismatch)
            template_doc = self.mongo.get_template_by_id(template_id=template_id, client_id=client_id)
            extracted = template_doc.get("extracted_structure", {})
            base_blueprint = {
                "client_id": client_id,
                "template_id": template_id,
                "template_name": template_doc.get("template_name"),
                "tiptap_schema_blueprint": extracted.get("tiptap_schema_blueprint", {}),
                "extracted_structure": extracted
            }
        else:
            base_blueprint = self.mongo.get_template(client_id=client_id)
            if not base_blueprint:
                base_blueprint = self.mongo._get_fallback_template(client_id=client_id)
        
        # Step 3: Run local tool compilation loop and call LLM context block
        compiled_tiptap_json = await self.tools.execute_in_app_loop(
            user_prompt=raw_user_prompt,
            context=historical_context,
            blueprint=base_blueprint
        )
        
        # Step 4: Dispatch the AI Critic using native FastAPI BackgroundTasks
        # This keeps user dashboard fast and lag-free without Celery/Redis
        background_tasks.add_task(
            self.critic.run_async_critic,
            client_id,
            compiled_tiptap_json
        )
        
        return compiled_tiptap_json

    async def synthesize_cross_app_search(
        self,
        client_id: str,
        query: str
    ) -> dict:
        """Queries MongoDB, HubSpot, GA4, QuickBooks, and SQLite DB concurrently, synthesizing unified search responses."""
        effective_gemini_key = get_effective_tenant_key(client_id, "Gemini", self.tools.sqlite_service)
        effective_mongo_uri = get_effective_tenant_key(client_id, "MongoDB", self.tools.sqlite_service)
        effective_hubspot_token = get_effective_tenant_key(client_id, "HubSpot", self.tools.sqlite_service)

        data_pool = {}
        sources = []

        q_lower = query.lower()

        # GA4 Metrics
        if any(k in q_lower for k in ["ga4", "traffic", "sessions", "pageviews", "analytics", "visitor"]):
            data_pool["ga4"] = get_ga4_metrics(client_id)
            sources.append("ga4")

        # QuickBooks Billing
        if any(k in q_lower for k in ["invoice", "quickbooks", "billing", "owe", "outstanding", "finance", "financial"]):
            data_pool["quickbooks"] = get_quickbooks_data(client_id)
            sources.append("quickbooks")

        # SQLite Vault Projects & Contacts
        if any(k in q_lower for k in ["project", "budget", "active", "campaign", "seo", "sqlite", "vault", "contact", "email", "phone", "person", "user"]):
            data_pool["projects"] = self.tools.sqlite_service.run_query("get_projects", {}, client_id)
            data_pool["contacts"] = self.tools.sqlite_service.run_query("get_contacts", {}, client_id)
            sources.append("database")

        # MongoDB CRM Notes & Contracts
        if any(k in q_lower for k in ["mongo", "mongodb", "crm", "note", "contract", "agreement", "renewal", "review", "alignment"]):
            data_pool["mongodb"] = self.mongo.search_records(client_id, query)
            sources.append("mongodb")

        # HubSpot Deals & Pipeline
        if any(k in q_lower for k in ["hubspot", "deal", "pipeline", "lead", "owner", "stage", "acme", "retainer", "expansion"]):
            data_pool["hubspot"] = get_hubspot_data(client_id)
            sources.append("hubspot")

        # Fallback: aggregate across all 5 integrated services if no keyword matched
        if not sources:
            data_pool["ga4"] = get_ga4_metrics(client_id)
            data_pool["quickbooks"] = get_quickbooks_data(client_id)
            data_pool["projects"] = self.tools.sqlite_service.run_query("get_projects", {}, client_id)
            data_pool["mongodb"] = self.mongo.search_records(client_id, query)
            data_pool["hubspot"] = get_hubspot_data(client_id)
            sources = ["ga4", "quickbooks", "database", "mongodb", "hubspot"]

        # Synthesize with Gemini LLM using dynamic effective tenant key if available
        if effective_gemini_key:
            genai.configure(api_key=effective_gemini_key)
            prompt = (
                "You are an operations summary assistant. "
                f"Synthesize a clear, short plain text answer specifically answering the user query: '{query}'.\n"
                f"Client ID: {client_id}\n"
                f"Retrieved Metrics & Multi-System Context Data: {json.dumps(data_pool)}\n"
                "Return only a concise, direct answer based strictly on the retrieved data."
            )
            for m_name in ["gemini-1.5-flash", "gemini-2.5-flash"]:
                clean_name = m_name.replace("models/", "")
                try:
                    model = genai.GenerativeModel(clean_name)
                    response = model.generate_content(contents=prompt)
                    if response and response.text:
                        return {
                            "status": "success",
                            "answer": response.text.strip(),
                            "sources_consulted": list(dict.fromkeys(sources))
                        }
                except Exception:
                    pass

        # Dynamic fallback synthesis logic when LLM key is absent or call fails
        answers = []
        if "ga4" in data_pool and data_pool["ga4"]:
            m = data_pool["ga4"][0] if isinstance(data_pool["ga4"], list) and data_pool["ga4"] else {}
            answers.append(f"GA4 recorded {m.get('sessions', 0):,} sessions")

        if "quickbooks" in data_pool and data_pool["quickbooks"]:
            qb = data_pool["quickbooks"]
            answers.append(f"outstanding QuickBooks invoices total ${qb.get('outstanding_invoices_total', 0.0):,.2f}")

        if "projects" in data_pool and data_pool["projects"]:
            p_names = [p.get("project_name") for p in data_pool["projects"] if p.get("project_name")]
            answers.append(f"vault active projects include {', '.join(p_names)}")

        if "mongodb" in data_pool and data_pool["mongodb"]:
            m_count = len(data_pool["mongodb"])
            answers.append(f"{m_count} MongoDB CRM notes/contract record(s) on file")

        if "hubspot" in data_pool and data_pool["hubspot"]:
            hb = data_pool["hubspot"]
            deals = hb.get("active_deals", [])
            owner = hb.get("account_owner", "Alice Miller")
            pipe_val = hb.get("total_pipeline_value", 0.0)
            answers.append(f"HubSpot pipeline totals ${pipe_val:,.2f} across {len(deals)} active deal(s) (Owner: {owner})")

        final_answer = f"For query '{query}' ({client_id}): " + ", while ".join(answers) + "."
        return {
            "status": "success",
            "answer": final_answer,
            "sources_consulted": list(dict.fromkeys(sources))
        }
