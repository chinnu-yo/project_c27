from typing import List, Literal
from pydantic import BaseModel

class CrossAppSearchRequestModel(BaseModel):
    client_id: str
    query_string: str

class CrossAppSearchResponseModel(BaseModel):
    status: Literal["success"]
    answer: str
    sources_consulted: List[str]
