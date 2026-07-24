import json
from fastapi import APIRouter, Depends
import google.generativeai as genai
from backend.app.core.config import settings
from backend.app.api.dependencies import get_mongo_service
from backend.app.services.mongo_service import MongoService
from backend.app.mcp_mocks.ga4_mock import get_ga4_metrics
from backend.app.mcp_mocks.quickbooks_mock import get_quickbooks_data
from backend.app.services.sqlite_service import SQLiteService
from backend.app.schemas.search_schemas import CrossAppSearchRequestModel, CrossAppSearchResponseModel

router = APIRouter()
sqlite_service = SQLiteService()

@router.post("/search", response_model=CrossAppSearchResponseModel)
async def cross_app_search(
    payload: CrossAppSearchRequestModel,
    mongo: MongoService = Depends(get_mongo_service)
):
    """Global cross-app search query aggregating mock pipelines and local SQLite data."""
    client_id = payload.client_id
    raw_query = payload.query or payload.query_string or ""
    query = raw_query.lower()

    data_pool = {}
    sources = []

    # Simple matching checks to route queries dynamically
    if any(k in query for k in ["ga4", "traffic", "sessions", "pageviews", "analytics", "visitor"]):
        data_pool["ga4"] = get_ga4_metrics(client_id)
        sources.append("ga4")

    if any(k in query for k in ["invoice", "quickbooks", "billing", "owe", "outstanding", "finance", "financial"]):
        data_pool["quickbooks"] = get_quickbooks_data(client_id)
        sources.append("quickbooks")

    if any(k in query for k in ["project", "budget", "active", "campaign", "seo"]):
        data_pool["projects"] = sqlite_service.run_query("get_projects", {}, client_id)
        sources.append("database")

    if any(k in query for k in ["contact", "email", "phone", "client", "person", "user"]):
        data_pool["contacts"] = sqlite_service.run_query("get_contacts", {}, client_id)
        sources.append("database")

    # If no specific key is triggered, aggregate all metrics for comprehensive overview
    if not sources:
        data_pool["ga4"] = get_ga4_metrics(client_id)
        data_pool["quickbooks"] = get_quickbooks_data(client_id)
        data_pool["projects"] = sqlite_service.run_query("get_projects", {}, client_id)
        sources = ["ga4", "quickbooks", "database"]

    # Synthesize answer using Gemini LLM if key is available
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
        prompt = (
            "You are an operations summary assistant. "
            f"Synthesize a clear, short plain text answer specifically answering the user query: '{raw_query}'.\n"
            f"Client ID: {client_id}\n"
            f"Retrieved Metrics context: {json.dumps(data_pool)}\n"
            "Return only a concise, direct answer based strictly on the retrieved data."
        )
        for m_name in ["gemini-1.5-flash", "gemini-2.5-flash"]:
            clean_name = m_name.replace("models/", "")
            try:
                model = genai.GenerativeModel(clean_name)
                response = model.generate_content(contents=prompt)
                if response and response.text:
                    return CrossAppSearchResponseModel(
                        status="success",
                        answer=response.text.strip(),
                        sources_consulted=list(dict.fromkeys(sources))
                    )
            except Exception:
                pass

    # Dynamic fallback synthesis logic when LLM key is absent or call fails
    answers = []
    if "ga4" in data_pool and data_pool["ga4"]:
        metrics = data_pool["ga4"][0] if isinstance(data_pool["ga4"], list) and data_pool["ga4"] else {}
        sessions = metrics.get("sessions", 0)
        pageviews = metrics.get("pageviews", 0)
        source_name = metrics.get("traffic_source", "search")
        answers.append(f"GA4 recorded {sessions:,} sessions ({pageviews:,} pageviews via {source_name})")

    if "quickbooks" in data_pool and data_pool["quickbooks"]:
        total = data_pool["quickbooks"].get("outstanding_invoices_total", 0.0)
        inv_count = data_pool["quickbooks"].get("invoice_count", 0)
        answers.append(f"outstanding QuickBooks invoices total ${total:,.2f} across {inv_count} invoice(s)")

    if "projects" in data_pool and data_pool["projects"]:
        projs = data_pool["projects"]
        names = [p.get("project_name") for p in projs if p.get("project_name")]
        if names:
            answers.append(f"active projects include {', '.join(names)}")
        else:
            answers.append(f"{len(projs)} active projects in vault")

    if "contacts" in data_pool and data_pool["contacts"]:
        conts = data_pool["contacts"]
        c_names = [c.get("contact_name") for c in conts if c.get("contact_name")]
        if c_names:
            answers.append(f"contacts on file: {', '.join(c_names)}")

    if answers:
        final_answer = f"For query '{raw_query}' ({client_id}): " + ", while ".join(answers) + "."
    else:
        final_answer = f"No workspace records found matching query '{raw_query}' for {client_id}."

    return CrossAppSearchResponseModel(
        status="success",
        answer=final_answer,
        sources_consulted=list(dict.fromkeys(sources))
    )
