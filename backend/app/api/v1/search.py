"""
Search API endpoints: Keyword and Semantic Search.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.search import SearchResponse
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_documents_api(
    q: str = Query(..., min_length=1, description="Search query string"),
    mode: str = Query("keyword", pattern="^(keyword|semantic)$", description="Search mode: keyword or semantic"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search indexed documents using keyword matching or semantic vector similarity.
    """
    return await search_service.search(query=q, mode=mode, db=db, limit=limit)
