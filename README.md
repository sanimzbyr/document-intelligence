# AI-Powered Document Intelligence System

A production-grade, end-to-end intelligent document processing (IDP) and financial audit system built with **FastAPI**, **Next.js 14**, **Celery + Redis**, **PostgreSQL 15 + pgvector**, and **OpenAI GPT-4o**.

Automates extraction of structured financial data from messy business documents (PDFs, images, Excel spreadsheets, CSVs), validates arithmetic consistency, prevents hallucinations, enables cross-document reconciliation, and provides hybrid keyword + semantic vector search.

---

## Key Capabilities

1. **Multi-Format Document Ingestion:**
   - Ingests single and multi-page **PDF**, **JPG**, **PNG**, **TIFF**, **XLSX**, **XLS**, and **CSV** files.
   - Dual-engine PDF processing: fast native digital extraction with `pdfplumber` + automatic OCR fallback with `pdf2image` and `pytesseract`.
   - Scalable chunked processing capable of handling 1,000+ page PDFs without memory crashes.
2. **Zero-Hallucination AI Extraction:**
   - Extracts `invoice_number`, `invoice_date`, `supplier_name`, `customer_name`, `subtotal`, `tax`, `total`, `currency`, and itemized `line_items`.
   - Uses OpenAI GPT-4o with strict JSON schema validation via Pydantic. Fields not explicitly present in the document are set to `null` rather than invented.
   - Built-in deterministic pattern extractor for offline/local evaluation without requiring active API keys.
3. **Automated Financial Validation & Cross-Reconciliation:**
   - Verifies arithmetic: `subtotal + tax == total` (±0.01 tolerance) and `sum(line_items) == subtotal`.
   - Duplicate detection: identifies duplicate invoice numbers for identical suppliers in the database.
   - Cross-Verification tool: reconciles disparate documents (e.g. comparing a PDF invoice against an Excel ledger).
   - Flags discrepancies automatically with `needs_review = true`.
4. **Interactive Reviewer Dashboard & Audit Trail:**
   - Modern Next.js 14 frontend with drag-and-drop batch upload, real-time polling status, and visual error indicators.
   - In-place editable form allowing human reviewers to modify extracted values and trigger instant re-validation.
   - Complete audit trail logging every modification (`old_value` → `new_value`, user, timestamp).
5. **Hybrid Keyword + Semantic Vector Search:**
   - Keyword search across metadata and extracted page texts.
   - Semantic search utilizing OpenAI vector embeddings (`text-embedding-3-small`) and cosine similarity.
6. **Production Testing & Measured Evaluation:**
   - 35 automated test cases with ≥70% coverage.
   - Empirical evaluation benchmark (`evaluation/run_eval.py`) evaluating 15 labeled documents across all formats, outputting `evaluation/report.md`.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons |
| **Backend API** | FastAPI (Python 3.12+), Pydantic v2, SlowAPI Rate Limiting, CORS |
| **OCR & PDF** | `pdfplumber`, `pypdf`, `pytesseract`, `pdf2image`, `Pillow` |
| **Spreadsheets** | `pandas`, `openpyxl` |
| **AI / LLM** | Google Gemini (`gemini-flash-lite-latest`), Groq, OpenRouter, or OpenAI |
| **Database & ORM** | PostgreSQL 15 + `pgvector` (SQLite fallback for single-node dev), SQLAlchemy 2.0 Async |
| **Task Queue** | Celery + Redis (with synchronous eager execution mode fallback) |
| **Auth** | JWT (JSON Web Tokens) with bcrypt password hashing |
| **Testing** | `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` |
| **DevOps** | Docker, Docker Compose, Makefile |

---

## Deliverables & Submission Index

All 9 required deliverables are organized and documented within this repository:

| # | Required Deliverable | Repository Location | Summary |
| :-: | :--- | :--- | :--- |
| **1** | **Git Repository** | Root directory (`.git/`, `main` branch) | Clean, atomic commit history |
| **2** | **README & Setup** | [`README.md`](./README.md) | Docker & local setup, prerequisites |
| **3** | **Architecture & Schema** | [`docs/architecture.md`](./docs/architecture.md) & [`docs/schema.md`](./docs/schema.md) | Mermaid diagrams, ER specifications |
| **4** | **Backend & Frontend** | [`backend/`](./backend/) & [`frontend/`](./frontend/) | FastAPI (Port 8000) & Next.js 14 (Port 3000) |
| **5** | **Multi-Format Pipelines** | [`backend/app/pipelines/`](./backend/app/pipelines/) | PDF (`pdfplumber`/OCR), Excel, CSV, Images |
| **6** | **Automated Tests** | [`docs/test_results.md`](./docs/test_results.md) & [`backend/tests/`](./backend/tests/) | 38 passed tests, 72% coverage (`make test`) |
| **7** | **Evaluation Report** | [`evaluation/report.md`](./evaluation/report.md) | 15 benchmark docs, 100% success rate, 0.91s latency |
| **8** | **Recorded Walkthrough** | [Watch the video](https://drive.google.com/file/d/1ydKOY617EEUGpzvoK7AmOoFbjuO06ZZY/view?usp=drive_link) | Video demonstration |
| **9** | **AI Prompts & Disclosure** | [`docs/ai_disclosure.md`](./docs/ai_disclosure.md) & [`PROMPT.md`](./PROMPT.md) | Prompts, grounding, and engineering disclosure |

---

## Repository Structure

```
document-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Route handlers: auth, documents, search
│   │   ├── core/           # config, database, security, celery
│   │   ├── models/         # SQLAlchemy 2.0 models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── pipelines/      # Text extraction & orchestrator
│   │   ├── services/       # AI extraction, validation, search, storage
│   │   ├── workers/        # Celery background tasks
│   │   ├── prompts/        # Externalized LLM prompts
│   │   ├── utils/          # File detection, structured JSON logger
│   │   └── main.py         # FastAPI application entrypoint
│   ├── scripts/
│   │   └── seed_demo.py    # Database & demo synthetic documents generator
│   ├── tests/              # 35 test cases (unit, integration, API)
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                # Next.js App Router (dashboard, detail, search, auth)
│   ├── components/         # FileUpload, DocumentTable, ExtractedDataForm, etc.
│   ├── lib/api.ts          # Strongly-typed API client
│   ├── package.json
│   └── Dockerfile
├── storage/                # Uploaded documents directory
├── evaluation/
│   ├── labeled_dataset/    # 15 sample documents across formats + ground_truth.json
│   ├── run_eval.py         # Evaluation benchmark runner
│   └── report.md           # Measured empirical accuracy & latency report
├── docs/
│   ├── architecture.md     # Architecture overview with Mermaid diagram
│   ├── schema.md           # Database ER diagram & table specifications
│   ├── decisions.md        # Architectural decisions and trade-offs
│   └── ai_disclosure.md    # Disclosure of AI assistance and prompts
├── docker-compose.yml       # Production one-command startup
├── Makefile                # Dev, test, eval, and migration tasks
├── .env.example
└── README.md
```

---

## Quickstart via Docker Compose

To spin up the entire production stack (PostgreSQL + pgvector, Redis, FastAPI Backend, Celery Worker, and Next.js Frontend):

```bash
# 1. Clone repository and navigate to folder
cd document-intelligence

# 2. Configure environment variables (optional: add your OPENAI_API_KEY)
cp .env.example .env

# 3. Start all services with one command
docker compose up --build
```

- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **API Documentation (Swagger UI):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **API Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Local Development (Without Docker)

You can run the system natively using the included `Makefile`:

### 1. Setup Virtual Environment
```bash
make setup
```

### 2. Seed Database with Demo Invoices & Users
```bash
./backend/venv/bin/python backend/scripts/seed_demo.py
```
*Creates default demo account: `admin@company.com` / `admin123` and ingests sample PDF, Excel, CSV, and image documents.*

### 3. Start Backend API
```bash
make dev
```
*Runs FastAPI with auto-reload on `http://localhost:8000`.*

### 4. Start Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
*Accessible on `http://localhost:3000`.*

---

## Automated Testing & Coverage

Run the comprehensive test suite with coverage report:

```bash
make test
```

**Results:**
- **38 passed tests** (0 failures).
- **Coverage: 72%** across core application modules (meets ≥ 70% requirement).
- Complete breakdown recorded in [`docs/test_results.md`](./docs/test_results.md).

---

## Free LLM API & Live Diagnostics

Test and verify the configured free LLM provider (Google Gemini or Groq):

```bash
# Direct diagnostic test
backend/venv/bin/python scripts/test_llm.py

# Or via HTTP health endpoint
curl http://localhost:8000/health/llm
```

---

## Evaluation Benchmark

Execute the empirical evaluation runner against the 15-document labeled dataset:

```bash
make eval
```

Generates [`evaluation/report.md`](./evaluation/report.md) detailing:
- **Document Success Rate:** 100.0%
- **Failure Rate:** 0.0%
- **Average Latency:** 0.913s per document
- **P95 Latency:** 1.365s
- **Extraction Accuracy:** 80.0% across all evaluated fields on heterogeneous files (100% on digital invoices).

---

## REST API Reference Summary

All endpoints are prefixed under `/api/v1`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and status |
| `POST` | `/auth/register` | Register new reviewer account |
| `POST` | `/auth/login` | Authenticate and obtain JWT bearer token |
| `GET` | `/auth/me` | Fetch authenticated user profile |
| `POST` | `/documents/upload` | Multipart file upload (single or multiple) |
| `GET` | `/documents` | List documents with status/supplier filters & pagination |
| `GET` | `/documents/{id}` | Full document detail (text, extracted data, validation errors) |
| `GET` | `/documents/{id}/status` | Check processing status & progress percentage for polling |
| `POST` | `/documents/{id}/reprocess` | Re-queue document for re-processing |
| `PATCH` | `/documents/{id}/extracted` | Apply manual field corrections & re-run validation |
| `POST` | `/documents/cross-verify` | Reconcile primary vs reference document (PDF vs Excel) |
| `GET` | `/search` | Query documents by keyword or semantic vector search |
