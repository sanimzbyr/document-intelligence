"""
Search Service.
Provides full-text keyword search and OpenAI semantic vector search with cosine similarity.
"""
import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from openai import AsyncOpenAI
from app.core.config import settings
from app.models.models import Document, ExtractedText, ExtractedData
from app.schemas.document import DocumentResponse, ExtractedInvoiceData, LineItem
from app.schemas.search import SearchResponse, SearchResultItem
from app.utils.logger import logger


class SearchService:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ("mock-or-real-api-key", "your-openai-api-key-here"):
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for text using OpenAI."""
        if not self.client or not text or not text.strip():
            return None
        try:
            res = await self.client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text[:8000]
            )
            return res.data[0].embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return None

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    async def search(
        self,
        query: str,
        mode: str,
        db: AsyncSession,
        limit: int = 20
    ) -> SearchResponse:
        """Execute keyword or semantic search across documents."""
        query = query.strip()
        results: List[SearchResultItem] = []

        if not query:
            return SearchResponse(query=query, mode=mode, total=0, results=[])

        if mode == "semantic":
            results = await self._semantic_search(query, db, limit)
        else:
            results = await self._keyword_search(query, db, limit)

        return SearchResponse(
            query=query,
            mode=mode,
            total=len(results),
            results=results
        )

    async def _keyword_search(self, query: str, db: AsyncSession, limit: int) -> List[SearchResultItem]:
        """Perform case-insensitive keyword search on text and extracted fields."""
        term = f"%{query}%"

        stmt = (
            select(Document, ExtractedText, ExtractedData)
            .outerjoin(ExtractedText, Document.id == ExtractedText.document_id)
            .outerjoin(ExtractedData, Document.id == ExtractedData.document_id)
            .where(
                or_(
                    Document.filename.ilike(term),
                    ExtractedText.text.ilike(term),
                    ExtractedData.invoice_number.ilike(term),
                    ExtractedData.supplier_name.ilike(term),
                    ExtractedData.customer_name.ilike(term),
                    ExtractedData.notes.ilike(term)
                )
            )
            .limit(limit)
        )

        rows = (await db.execute(stmt)).all()
        seen_docs = set()
        items: List[SearchResultItem] = []

        for doc, ext_text, ext_data in rows:
            if doc.id in seen_docs:
                continue
            seen_docs.add(doc.id)

            snippet = "Match found in document metadata."
            if ext_text and ext_text.text and query.lower() in ext_text.text.lower():
                idx = ext_text.text.lower().find(query.lower())
                start = max(0, idx - 50)
                end = min(len(ext_text.text), idx + len(query) + 50)
                snippet = f"...{ext_text.text[start:end]}..."
            elif ext_data:
                snippet = f"Match in invoice #{ext_data.invoice_number or 'N/A'}, Supplier: {ext_data.supplier_name or 'N/A'}"

            extracted_schema = None
            if ext_data:
                extracted_schema = ExtractedInvoiceData(
                    invoice_number=ext_data.invoice_number,
                    invoice_date=ext_data.invoice_date,
                    supplier_name=ext_data.supplier_name,
                    customer_name=ext_data.customer_name,
                    subtotal=ext_data.subtotal,
                    tax=ext_data.tax,
                    total=ext_data.total,
                    currency=ext_data.currency,
                    line_items=[LineItem(**item) for item in (ext_data.line_items or []) if isinstance(item, dict)],
                    confidence=ext_data.confidence,
                    notes=ext_data.notes
                )

            items.append(SearchResultItem(
                document=DocumentResponse.model_validate(doc),
                extracted_data=extracted_schema,
                snippet=snippet,
                score=1.0,
                match_type="keyword"
            ))

        return items

    async def _semantic_search(self, query: str, db: AsyncSession, limit: int) -> List[SearchResultItem]:
        """Perform semantic search using vector cosine similarity."""
        query_vector = await self.get_embedding(query)
        if not query_vector:
            logger.info("Semantic embedding unavailable, falling back to keyword search.")
            return await self._keyword_search(query, db, limit)

        # Retrieve documents and their stored page embeddings
        stmt = (
            select(Document, ExtractedText, ExtractedData)
            .join(ExtractedText, Document.id == ExtractedText.document_id)
            .outerjoin(ExtractedData, Document.id == ExtractedData.document_id)
            .where(ExtractedText.embedding.isnot(None))
        )

        rows = (await db.execute(stmt)).all()
        scored_items = []

        for doc, ext_text, ext_data in rows:
            if not ext_text.embedding or not isinstance(ext_text.embedding, list):
                continue
            sim = self.cosine_similarity(query_vector, ext_text.embedding)
            if sim > 0.30:  # Relevance threshold
                snippet = (ext_text.text[:150] + "...") if ext_text.text else ""
                extracted_schema = None
                if ext_data:
                    extracted_schema = ExtractedInvoiceData(
                        invoice_number=ext_data.invoice_number,
                        invoice_date=ext_data.invoice_date,
                        supplier_name=ext_data.supplier_name,
                        customer_name=ext_data.customer_name,
                        subtotal=ext_data.subtotal,
                        tax=ext_data.tax,
                        total=ext_data.total,
                        currency=ext_data.currency,
                        line_items=[LineItem(**item) for item in (ext_data.line_items or []) if isinstance(item, dict)],
                        confidence=ext_data.confidence,
                        notes=ext_data.notes
                    )

                scored_items.append((
                    sim,
                    SearchResultItem(
                        document=DocumentResponse.model_validate(doc),
                        extracted_data=extracted_schema,
                        snippet=snippet,
                        score=round(sim, 4),
                        match_type="semantic"
                    )
                ))

        # Sort descending by similarity score
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_items[:limit]]


search_service = SearchService()
