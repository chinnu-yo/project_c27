from fastapi import APIRouter
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.orchestrate import router as orchestrate_router
from backend.app.api.v1.endpoints.memory import router as memory_router
from backend.app.api.v1.endpoints.reports import router as reports_router
from backend.app.api.v1.endpoints.search import router as search_router
from backend.app.api.v1.endpoints.templates import router as templates_router
from backend.app.api.v1.endpoints.integrations import router as integrations_router
from backend.app.api.v1.endpoints.team import router as team_router

api_router = APIRouter()

# Mount endpoints matching api_contracts.md paths under prefix /api/v1
api_router.include_router(auth_router)
api_router.include_router(orchestrate_router)
api_router.include_router(memory_router)
api_router.include_router(reports_router)
api_router.include_router(search_router)
api_router.include_router(templates_router)
api_router.include_router(integrations_router)
api_router.include_router(team_router)

