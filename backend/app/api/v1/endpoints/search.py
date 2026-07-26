import json
from fastapi import APIRouter, Depends
import google.generativeai as genai
from backend.app.core.config import settings
from backend.app.api.dependencies import get_orchestrator
from backend.app.services.orchestrator import OrchestrationEngine
from backend.app.schemas.search_schemas import CrossAppSearchRequestModel, CrossAppSearchResponseModel

router = APIRouter()

@router.post("/search", response_model=CrossAppSearchResponseModel)
async def cross_app_search(
    payload: CrossAppSearchRequestModel,
    engine: OrchestrationEngine = Depends(get_orchestrator)
):
    """Global cross-app search query aggregating GA4, QuickBooks, SQLite, MongoDB, and HubSpot pipelines."""
    client_id = payload.client_id
    raw_query = payload.query or payload.query_string or ""

    result = await engine.synthesize_cross_app_search(
        client_id=client_id,
        query=raw_query
    )

    return CrossAppSearchResponseModel(
        status="success",
        answer=result["answer"],
        sources_consulted=result["sources_consulted"]
    )
