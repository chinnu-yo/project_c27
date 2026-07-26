from pydantic import BaseModel, Field
from typing import List, Optional

class InviteTeamMemberRequestModel(BaseModel):
    email: str = Field(..., description="Team member email address")
    role: str = Field(default="Member", description="Admin or Member")
    client_access: List[str] = Field(default_factory=list)

class UpdateTeamMemberRequestModel(BaseModel):
    role: str = Field(..., description="Admin or Member")
    client_access: List[str] = Field(default_factory=list)

class TeamMemberResponseModel(BaseModel):
    id: str
    email: str
    role: str
    client_access: List[str]
    status: str
    created_at: int

class TeamMembersListResponseModel(BaseModel):
    status: str
    members: List[TeamMemberResponseModel]
