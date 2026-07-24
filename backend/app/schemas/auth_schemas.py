from pydantic import BaseModel


class LoginRequestModel(BaseModel):
    client_id: str
    password: str


class LoginResponseModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
    client_id: str
