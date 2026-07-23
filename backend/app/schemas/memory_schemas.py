from typing import Optional, Literal
from pydantic import BaseModel

class MemoryValidateRequestModel(BaseModel):
    notification_id: str
    client_id: str
    action: Literal["approve", "reject"]
    extracted_fact: str
    domain: Literal["formatting_preference", "accounting_logic", "metric_definitions"]

class MemoryValidateResponseModel(BaseModel):
    status: Literal["success"]
    notification_id: str
    current_state: Literal["approved", "rejected"]
    chroma_id: Optional[str] = None
