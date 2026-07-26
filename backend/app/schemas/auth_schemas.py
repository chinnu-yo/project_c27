from typing import List, Optional
from pydantic import BaseModel


class LoginRequestModel(BaseModel):
    client_id: str
    password: str
    user_role: Optional[str] = "Admin"


class LoginResponseModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
    client_id: str
    user_role: str = "Admin"
    assigned_tenants: List[str] = ["client_abc", "client_xyz"]
