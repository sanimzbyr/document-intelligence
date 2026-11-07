"""
Search request and response Pydantic schemas.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.document import DocumentResponse, ExtractedInvoiceData


class SearchResultItem(BaseModel):
    document: DocumentResponse
    extracted_data: Optional[ExtractedInvoiceData] = None
    snippet: str
    score: float = Field(default=1.0, description="Relevance or similarity score")
    match_type: str = Field(..., description="keyword or semantic")


class SearchResponse(BaseModel):
    query: str
    mode: str  # keyword, semantic, hybrid
    total: int
    results: List[SearchResultItem]
