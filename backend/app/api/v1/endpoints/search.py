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
    query = payload.query_string.lower()

    data_pool = {}
    sources = []

    # Simple matching checks to route queries dynamically
    if any(k in query for k in ["ga4", "traffic", "sessions", "pageviews"]):
        data_pool["ga4"] = get_ga4_metrics(client_id)
        sources.append("ga4")

    if any(k in query for k in ["invoice", "quickbooks", "billing", "owe", "outstanding"]):
        data_pool["quickbooks"] = get_quickbooks_data(client_id)
        sources.append("quickbooks")

    if any(k in query for k in ["project", "budget", "active"]):
        data_pool["projects"] = sqlite_service.run_query("get_projects", {}, client_id)
        sources.append("database")

    if any(k in query for k in ["contact", "email", "phone"]):
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
        try:
            prompt = (
                "You are an operations summary assistant. "
                "Synthesize a clear, short plain text answer answering the user query. "
                f"User query: '{payload.query_string}'\n"
                f"Client ID: {client_id}\n"
                f"Retrieved Metrics context: {json.dumps(data_pool)}\n"
                "Return only a single short sentence answering the query directly based on the data."
            )
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(contents=prompt)
            return CrossAppSearchResponseModel(
                status="success",
                answer=response.text.strip(),
                sources_consulted=sources
            )
        except Exception:
            pass

    # Fallback sandbox synthesis logic
    answers = []
    if "ga4" in data_pool and data_pool["ga4"]:
        sessions = data_pool["ga4"][0].get("sessions", 0)
        answers.append(f"GA4 recorded {sessions:,} sessions")
    if "quickbooks" in data_pool and data_pool["quickbooks"]:
        total = data_pool["quickbooks"].get("outstanding_invoices_total", 0.0)
        answers.append(f"outstanding QuickBooks invoices total ${total:,.2f}")
    if "projects" in data_pool and data_pool["projects"]:
        proj_count = len(data_pool["projects"])
        answers.append(f"{proj_count} active projects in the vault")

    final_answer = f"For {client_id} this month: " + ", while ".join(answers) + "."
    return CrossAppSearchResponseModel(
        status="success",
        answer=final_answer,
        sources_consulted=sources
    )
