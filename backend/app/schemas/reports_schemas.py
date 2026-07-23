from typing import Literal
from pydantic import BaseModel
from backend.app.schemas.orchestrate_schemas import TiptapDocContainer

class SaveReportRequestModel(BaseModel):
    client_id: str
    report_name: str
    tiptap_json: TiptapDocContainer

class SaveReportResponseModel(BaseModel):
    status: Literal["success"]
    report_id: str
    saved_at: int
