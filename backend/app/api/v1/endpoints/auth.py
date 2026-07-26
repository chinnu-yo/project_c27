from fastapi import APIRouter, Depends
from backend.app.api.dependencies import get_sqlite_service
from backend.app.services.sqlite_service import SQLiteService
from backend.app.schemas.auth_schemas import LoginRequestModel, LoginResponseModel
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.exceptions import SecurityError

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponseModel)
async def login(
    payload: LoginRequestModel,
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Authenticates client credentials against SQLite and issues a signed JWT token with role claims."""
    if not payload.client_id or not payload.password:
        raise SecurityError("Invalid client credentials")

    creds = sqlite.get_client_credentials(payload.client_id)
    if not creds:
        raise SecurityError("Invalid client credentials")

    stored_hash = creds.get("password_hash")
    if not stored_hash or not verify_password(payload.password, stored_hash):
        raise SecurityError("Invalid client credentials")

    # Determine role claim from request payload or default to Admin
    role = payload.user_role if payload.user_role else "Admin"
    if role.lower() in ["admin", "admin / manager"]:
        assigned_role = "Admin"
    else:
        assigned_role = "Member"

    assigned_tenants = ["client_abc", "client_xyz"]

    token = create_access_token(
        client_id=payload.client_id,
        user_role=assigned_role,
        assigned_tenants=assigned_tenants
    )
    return LoginResponseModel(
        access_token=token,
        token_type="bearer",
        client_id=payload.client_id,
        user_role=assigned_role,
        assigned_tenants=assigned_tenants
    )
