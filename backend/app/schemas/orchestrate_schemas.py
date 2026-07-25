from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class TiptapNodeModel(BaseModel):
    type: str
    attrs: Optional[Dict[str, Any]] = None
    content: Optional[List['TiptapNodeModel']] = None
    text: Optional[str] = None
    marks: Optional[List[Dict[str, Any]]] = None

class TiptapDocContainer(BaseModel):
    type: Literal["doc"]
    content: List[TiptapNodeModel]

class OrchestrateRequestModel(BaseModel):
    client_id: str = Field(..., example="client_abc")
    user_prompt: str = Field(..., example="Generate the Q3 performance report")
    template_id: Optional[str] = Field(None, example="tmpl_12345678")

class OrchestrateResponseModel(BaseModel):
    status: Literal["success", "error"]
    injected_facts_count: int
    generated_system_prompt: str
    tiptap_json: TiptapDocContainer
