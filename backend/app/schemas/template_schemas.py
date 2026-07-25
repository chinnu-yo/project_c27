from typing import List, Optional
from pydantic import BaseModel, Field

class TemplateMetadataResponse(BaseModel):
    template_id: str
    client_id: str
    template_name: str
    description: str
    original_filename: str
    file_type: str
    uploaded_at: int

class TemplateListResponse(BaseModel):
    status: str = "success"
    templates: List[TemplateMetadataResponse]

class TemplateUploadResponse(BaseModel):
    status: str = "success"
    template_id: str
    template_name: str
    message: str
