from pydantic import BaseModel, Field
from typing import Optional, List

class CreateIntegrationRequestModel(BaseModel):
    client_id: str
    integration_name: str = Field(..., min_length=1)
    integration_type: str = Field(..., description="api_key, connection_string, or oauth")
    endpoint_url: str = Field(..., min_length=1)
    credential: str = Field(..., min_length=1)

class IntegrationResponseModel(BaseModel):
    id: str
    client_id: str
    integration_name: str
    integration_type: str
    endpoint_url: str
    masked_credential: str
    created_at: int
    last_tested_at: Optional[int] = None
    last_test_status: str

class IntegrationsListResponseModel(BaseModel):
    status: str
    client_id: str
    integrations: List[IntegrationResponseModel]

class TestIntegrationResponseModel(BaseModel):
    status: str
    message: str
    verification_details: str
    last_tested_at: int
