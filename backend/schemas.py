from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query: str

class SourceItem(BaseModel):
    doc_id: str
    text: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
