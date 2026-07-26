import time
import uuid
from fastapi import APIRouter, Depends
from backend.app.core.exceptions import ValidationError, SecurityError
from backend.app.api.dependencies import get_sqlite_service, verify_admin_role, get_current_client_id
from backend.app.services.sqlite_service import SQLiteService
from backend.app.schemas.team_schemas import (
    InviteTeamMemberRequestModel,
    UpdateTeamMemberRequestModel,
    TeamMemberResponseModel,
    TeamMembersListResponseModel
)

router = APIRouter()

@router.get("/team/list", response_model=TeamMembersListResponseModel)
async def list_team_members(
    client_id: str,
    auth_client_id: str = Depends(get_current_client_id),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Lists all registered and pending team members."""
    if client_id != auth_client_id:
        raise SecurityError("Tenant isolation mismatch: Cannot view team members for another client_id.")

    members = sqlite.get_team_members()
    res_items = []
    for m in members:
        res_items.append(TeamMemberResponseModel(
            id=m["id"],
            email=m["email"],
            role=m["role"],
            client_access=m.get("client_access", []),
            status=m.get("status", "active"),
            created_at=m.get("created_at", int(time.time()))
        ))

    return TeamMembersListResponseModel(
        status="success",
        members=res_items
    )

@router.post("/team/invite", response_model=TeamMemberResponseModel)
async def invite_team_member(
    payload: InviteTeamMemberRequestModel,
    admin_claims: dict = Depends(verify_admin_role),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Invites a new team member by email (Admin-only). Stores pending record."""
    existing = sqlite.get_team_member_by_email(str(payload.email))
    if existing:
        raise ValidationError(f"Team member with email '{payload.email}' already exists.")

    member_id = f"tm_{uuid.uuid4().hex[:10]}"
    created_at = int(time.time())

    created = sqlite.create_team_member(
        member_id=member_id,
        email=str(payload.email),
        role=payload.role,
        client_access=payload.client_access,
        status="pending",
        created_at=created_at
    )

    return TeamMemberResponseModel(
        id=created["id"],
        email=created["email"],
        role=created["role"],
        client_access=created.get("client_access", []),
        status=created["status"],
        created_at=created["created_at"]
    )

@router.put("/team/{member_id}", response_model=TeamMemberResponseModel)
async def update_team_member(
    member_id: str,
    payload: UpdateTeamMemberRequestModel,
    admin_claims: dict = Depends(verify_admin_role),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Updates team member role and client access permissions (Admin-only)."""
    updated = sqlite.update_team_member(
        member_id=member_id,
        role=payload.role,
        client_access=payload.client_access
    )

    if not updated:
        raise ValidationError(f"Team member with ID '{member_id}' not found.")

    return TeamMemberResponseModel(
        id=updated["id"],
        email=updated["email"],
        role=updated["role"],
        client_access=updated.get("client_access", []),
        status=updated.get("status", "active"),
        created_at=updated.get("created_at", int(time.time()))
    )

@router.delete("/team/{member_id}")
async def remove_team_member(
    member_id: str,
    admin_claims: dict = Depends(verify_admin_role),
    sqlite: SQLiteService = Depends(get_sqlite_service)
):
    """Removes a team member (Admin-only)."""
    deleted = sqlite.delete_team_member(member_id)
    if not deleted:
        raise ValidationError(f"Team member with ID '{member_id}' not found.")

    return {"status": "success", "message": f"Team member '{member_id}' removed successfully."}
