# Architectural Decisions and Engineering Trade-Offs

## 1. Unified Python Backend vs. Multi-Language Microservices
- **Decision:** Build the entire backend API and worker pipeline in Python (FastAPI + Celery + SQLAlchemy 2.0).
- **Rationale:** Python possesses the most mature and battle-tested ecosystem for document intelligence (`pdfplumber`, `pytesseract`, `pdf2image`, `pandas`, `openpyxl`, `reportlab`, and OpenAI SDK). Building a separate Node.js service would have introduced unnecessary inter-process serialization overhead and split the data models across two runtimes without performance benefit.

## 2. Deterministic Arithmetic Verification vs. LLM Calculations
- **Decision:** Use LLMs strictly for entity extraction and language understanding, while running mathematical validation (`subtotal + tax == total`, `sum(line_items) == subtotal`, tolerance checks) using deterministic Python code.
- **Rationale:** LLMs are known to hallucinate arithmetic operations and can fail subtle rounding or floating-point nuances. Keeping arithmetic deterministic guarantees 100% mathematical auditability.

## 3. Large Document Handling (1,000+ Pages)
- **Decision:** Process multi-page PDFs iteratively page-by-page, chunking extracted text into discrete records linked to page numbers.
- **Rationale:** Loading a 1,000-page document into a single memory buffer or sending it in one prompt to an LLM will exhaust token limits and trigger `OutOfMemoryError` crashes. By processing pages iteratively and storing individual embeddings, users can search across specific pages while staying within token limits.

## 4. Multi-Modal Dual-Engine PDF Ingestion
- **Decision:** First attempt native digital text extraction via `pdfplumber`. If the extracted character count is below 30 characters (or text is empty/garbled), trigger fallback OCR using `pdf2image` and `pytesseract` with image preprocessing.
- **Rationale:** Native digital extraction is 50x faster and requires 95% less CPU than OCR. However, scanned PDFs contain only raster images. Dual-mode routing delivers maximum performance on clean PDFs while ensuring full coverage for scanned documents.

## 5. Dual Search Engine: PostgreSQL FTS + Vector Embeddings
- **Decision:** Implement hybrid search supporting exact keyword / token search and semantic vector search via OpenAI `text-embedding-3-small` and cosine similarity.
- **Rationale:** Users frequently search for exact alphanumeric tokens (e.g. `INV-2026-0042`) where semantic embeddings perform poorly due to embedding collisions. Conversely, conceptual queries like *"quarterly hosting bills"* require vector similarity. Offering both keyword and semantic modes provides the optimal retrieval strategy for every user intent.

## 6. Resilience and Local Standalone Execution
- **Decision:** Support both Docker Compose (PostgreSQL 15 + pgvector + Redis 7 + Celery workers) and local standalone execution (SQLite + in-process Celery eager mode).
- **Rationale:** Enables developers and reviewers to run the test suite (`make test`), evaluation benchmark (`make eval`), and local server (`make dev`) instantly without requiring external database or Redis daemons, while remaining 100% production-ready for Docker deployment.
