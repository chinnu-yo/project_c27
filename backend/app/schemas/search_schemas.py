from typing import List, Literal, Optional
from pydantic import BaseModel

class CrossAppSearchRequestModel(BaseModel):
    client_id: str
    query_string: Optional[str] = None
    query: Optional[str] = None

class CrossAppSearchResponseModel(BaseModel):
    status: Literal["success"]
    answer: str
    sources_consulted: List[str]
