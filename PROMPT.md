# Prompt: Build an AI-Powered Document Intelligence System

You are a senior full-stack engineer and AI engineer. Build a complete, production-quality "AI-Powered Document Intelligence System" from scratch. The system automates extraction of structured data from business documents (invoices, receipts, scanned PDFs, images, Excel, CSV) and makes it searchable via API + web UI.

---

## 1. Project Overview

A company receives thousands of business documents daily. Employees manually extract invoice details, verify calculations, and enter data into internal systems. Build an AI system that:

- Accepts multiple file types: PDF, JPG, PNG, TIFF, XLSX, XLS, CSV
- Extracts text (digital PDFs), OCRs scanned docs/images, parses spreadsheets
- Uses AI to extract structured invoice fields into JSON
- Validates data (missing fields, bad numbers, duplicates, math inconsistencies)
- Exposes REST APIs + background processing
- Stores data in DB with keyword + semantic search
- Provides a React/Next.js frontend
- Includes automated tests + evaluation report

---

## 2. Tech Stack (use these unless you justify an alternative)

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI (Python 3.11+) with async support
- **OCR:** pytesseract + pdf2image + Pillow (system: tesseract-ocr, poppler-utils)
- **PDF text:** pdfplumber (digital), fallback to OCR for scanned
- **Spreadsheets:** pandas + openpyxl
- **AI extraction:** OpenAI API (GPT-4o) with JSON mode / structured outputs
- **Database:** PostgreSQL 15 + pgvector extension
- **ORM:** SQLAlchemy 2.0 (async) + Alembic migrations
- **Background jobs:** Celery + Redis (broker + result backend)
- **File storage:** local filesystem under `./storage/` (abstracted via a storage service for S3 swap)
- **Embeddings:** OpenAI `text-embedding-3-small` for semantic search
- **Testing:** pytest + httpx (backend), Jest + React Testing Library (frontend)
- **Containerization:** Docker + docker-compose for one-command startup
- **Auth:** JWT-based simple auth (register/login) — keep it minimal but real

---

## 3. Repository Structure

```
document-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # config, security, database, celery
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/            # route handlers (v1)
│   │   ├── services/       # business logic (extraction, validation, search)
│   │   ├── pipelines/      # document processing pipeline stages
│   │   ├── workers/        # celery tasks
│   │   ├── prompts/        # extraction_prompt.txt, validation_prompt.txt
│   │   └── utils/
│   ├── scripts/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js app router
│   ├── components/
│   ├── lib/
│   └── ...
├── storage/                # uploaded files (gitignored)
├── evaluation/
│   ├── labeled_dataset/    # sample docs + ground truth JSON
│   ├── run_eval.py
│   └── report.md
├── docs/
│   ├── architecture.md
│   ├── schema.md
│   ├── decisions.md
│   ├── walkthrough.md
│   └── ai_disclosure.md
├── docker-compose.yml
├── Makefile
├── README.md
└── .env.example
```

---

## 4. Functional Requirements

### Task 1 — Document Processing
- Endpoint to upload one or many files (multipart).
- Detect file type by extension + magic bytes.
- Pipeline per file:
  1. Save file, create DB record (status = queued)
  2. Extract text:
     - PDF: try pdfplumber (digital). If text is empty/low-quality → render pages to images → OCR with pytesseract.
     - Image (JPG/PNG/TIFF): OCR directly. Handle low DPI by upscaling.
     - XLSX/XLS: pandas read all sheets → convert to text + structured rows.
     - CSV: pandas read → text + rows.
  3. Handle corrupt files: catch exceptions, mark status = failed, store error, allow reprocess.
  4. Multi-page PDFs: process each page, store per-page text.
  5. Store extracted text + metadata in DB.
- Background processing via Celery; status transitions: queued → processing → completed/failed.

### Task 2 — AI Information Extraction
- After text extraction, call LLM with a strict prompt to extract:
  `invoice_number, invoice_date, supplier_name, customer_name, subtotal, tax, total, currency, line_items[]`
  where line_items = `{description, quantity, unit_price, amount}`.
- Use OpenAI structured outputs / JSON mode. Validate the JSON with Pydantic.
- If a field is missing/uncertain → set to null, never invent. Include a `confidence` score and `notes` for uncertainties.
- Store structured result linked to document.

### Task 3 — Data Validation
- Rules:
  - Required fields present (invoice_number, date, total at minimum).
  - Numeric consistency: subtotal + tax ≈ total (tolerance 0.01).
  - Line items sum ≈ subtotal.
  - Duplicate invoice detection (same invoice_number + supplier within DB).
  - Date format validity.
  - Currency recognized.
- Output: list of validation errors with severity (error/warning), field, message.
- Flag record `needs_review = true` if any error/warning.
- Manual correction endpoint: PATCH extracted fields, re-run validation, log correction history.

### Task 4 — Backend API
Design REST API under `/api/v1`:

- `POST /documents/upload` — multipart upload (single or multiple), returns job IDs
- `GET /documents` — list with filters (status, date range, supplier, search query), pagination
- `GET /documents/{id}` — details: metadata, text, structured data, validation errors
- `GET /documents/{id}/status` — processing status + progress
- `POST /documents/{id}/reprocess` — re-run pipeline
- `PATCH /documents/{id}/extracted` — manual corrections
- `GET /search?q=&mode=keyword|semantic` — search documents
- `GET /health`
- Auth: `POST /auth/register`, `POST /auth/login` (JWT)

All endpoints return consistent JSON. Use Pydantic response models. Include OpenAPI docs (FastAPI auto).

### Task 5 — Database + Search
Tables:
- `users` (id, email, hashed_password, created_at)
- `documents` (id, user_id, filename, file_type, file_path, status, page_count, created_at, updated_at, error_message, needs_review)
- `extracted_text` (id, document_id, page_number, text, created_at)
- `extracted_data` (id, document_id, invoice_number, invoice_date, supplier_name, customer_name, subtotal, tax, total, currency, line_items JSONB, confidence, notes, raw_llm_response, created_at, updated_at)
- `validation_errors` (id, document_id, field, severity, message, created_at)
- `correction_history` (id, document_id, field, old_value, new_value, corrected_by, created_at)
- `processing_history` (id, document_id, stage, status, started_at, finished_at, error)

Search:
- Keyword: PostgreSQL full-text search (tsvector) on extracted text + fields.
- Semantic: embed document text → store in pgvector; cosine similarity search.

### Task 6 — Frontend (Next.js)
Pages:
- `/login`, `/register`
- `/dashboard` — upload widget (drag & drop multi-file), recent documents table with status badges
- `/documents/[id]` — tabs: Overview, Extracted Data (editable form), Validation Errors, Raw Text, Processing History
- `/search` — search bar with keyword/semantic toggle, results list
- Components: FileUpload, StatusBadge, DocumentTable, ExtractedDataForm, ValidationList, SearchBar
- Show processing progress (polling status every 2s while processing)
- Allow editing extracted fields + save (calls PATCH) + re-validate
- Responsive, clean UI with Tailwind + shadcn/ui

### Task 7 — Testing + Evaluation
Tests:
- Unit: OCR helper, PDF extraction, spreadsheet parsing, validation rules, LLM parsing (mocked).
- Integration: upload → process → extract → validate flow (use test DB).
- API: all endpoints (auth, upload, status, search, correction, reprocess).
- Failure scenarios: corrupt PDF, empty file, missing fields, bad numbers, duplicate invoice, oversized file.

Evaluation:
- Create `evaluation/labeled_dataset/` with 10-20 sample documents (PDF/image/Excel/CSV) + `ground_truth.json`.
- Write `evaluation/run_eval.py` that processes all, compares extracted vs ground truth, computes:
  - Per-field accuracy (exact + fuzzy match)
  - Overall document success rate
  - Processing time (avg, p95)
  - Failure rate
- Output `evaluation/report.md` with metrics table + notes.

---

## 5. Non-Functional Requirements

- Performance: process a 10-page PDF in < 30s; handle 1000-page PDFs via chunked processing.
- Scalability: Celery workers horizontally scalable; stateless API.
- Reliability: retries on transient LLM/OCR failures (3 attempts, exponential backoff); idempotent reprocessing.
- Security: validate file types & size (max 50MB), sanitize filenames, JWT auth, rate limiting on upload, SQL injection prevention via ORM, no secrets in code (use .env).
- Logging: structured logging (JSON) with request IDs; error tracking.
- Health check endpoint.
