from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.services.mongo_service import MongoService
from backend.app.services.chroma_service import ChromaMemoryLayer
from backend.app.services.local_tools import LocalToolsManager
from backend.app.services.critic_service import CriticService
from backend.app.services.orchestrator import OrchestrationEngine
from backend.app.services.sqlite_service import SQLiteService
from backend.app.core.exceptions import SecurityError
from backend.app.core.security import decode_access_token

# Shared singleton dependencies across the backend gateway instance
mongo_db = MongoService()
chroma_db = ChromaMemoryLayer()
tools_mgr = LocalToolsManager()
critic_mgr = CriticService()
sqlite_db = SQLiteService()

security_scheme = HTTPBearer(auto_error=False)

engine = OrchestrationEngine(
    chroma_client=chroma_db,
    mongo_client=mongo_db,
    local_tools=tools_mgr,
    critic_service=critic_mgr
)


def get_mongo_service() -> MongoService:
    return mongo_db


def get_chroma_service() -> ChromaMemoryLayer:
    return chroma_db


def get_orchestrator() -> OrchestrationEngine:
    return engine


def get_sqlite_service() -> SQLiteService:
    return sqlite_db


def get_critic_service() -> CriticService:
    return critic_mgr


def get_current_client_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """FastAPI dependency for validating JWT token in Authorization header."""
    if not credentials or not credentials.credentials:
        raise SecurityError("Authentication required: Missing token")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        client_id = payload.get("client_id")
        if not client_id:
            raise SecurityError("Invalid token payload: missing client_id claim")
        return client_id
    except Exception as e:
        if isinstance(e, SecurityError):
            raise e
        raise SecurityError(f"Invalid or expired authentication token: {str(e)}")


def verify_admin_role(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> dict:
    """FastAPI dependency for verifying caller has Admin role permissions."""
    if not credentials or not credentials.credentials:
        raise SecurityError("Authentication required: Missing token")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        # Check role claim directly or allow default tenant admin
        role = payload.get("role", "Admin")  # Default to Admin for tenant tokens
        user_email = payload.get("email")
        if user_email:
            member = sqlite_db.get_team_member_by_email(user_email)
            if member:
                role = member.get("role", role)
        
        if role != "Admin":
            raise SecurityError("Forbidden: Admin permissions required for this operation.")
        return payload
    except Exception as e:
        if isinstance(e, SecurityError):
            raise e
        raise SecurityError(f"Authorization error: {str(e)}")

