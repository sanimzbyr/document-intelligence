# Recorded Video Walkthrough Guide & Demonstration Script

This document provides a minute-by-minute demonstration script and checklist for recording the required video walkthrough of the **AI-Powered Document Intelligence System**.

> **Recommended Video Recording Tool:** [Loom](https://www.loom.com/) (free screen + webcam recorder) or [OBS Studio](https://obsproject.com/).  
> **Recommended Duration:** 4 to 6 minutes.  
> **Target Audience:** Technical evaluators, hiring managers, and AI system architects.

---

## 1. Pre-Recording Checklist

Before starting your recording:
1. **Ensure Services Are Running:**
   - Backend API: `http://localhost:8000` (FastAPI)
   - Frontend UI: `http://localhost:3000` (Next.js 14)
   - Health check verified: `curl http://localhost:8000/health/llm`
2. **Prepare Sample Test Files:**
   The evaluation dataset contains ready-to-use sample files under `evaluation/labeled_dataset/`:
   - `inv_acme_cloud.pdf` (Digital PDF Invoice)
   - `ledger_hardware_q1.xlsx` (Multi-sheet Excel Ledger)
   - `procurement_march_a.csv` (Tabular CSV Procurement)
   - `receipt_fuel_express.png` (Receipt Image)
3. **Open Browser Tabs:**
   - Tab 1: [http://localhost:3000](http://localhost:3000) (Dashboard)
   - Tab 2: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) (Swagger UI)
   - Tab 3: Terminal with repo root.

---

## 2. Minute-by-Minute Demonstration Script

### Segment 1: Introduction & Architecture Overview (0:00 - 0:45)
- **What to show on screen:** Code editor / architecture diagram (`docs/architecture.md`).
- **Talking points:**
  - *"Hello! Today I'm demonstrating our end-to-end AI-Powered Document Intelligence System."*
  - *"The architecture is decoupled for production scale: a Next.js 14 App Router frontend, an asynchronous FastAPI backend, Celery + Redis task queue for background workers, PostgreSQL 15 with pgvector, and Google Gemini Flash Lite for high-speed, zero-hallucination structured extraction."*
  - *"We also feature a deterministic mathematical validation engine and hybrid keyword/semantic search."*

---

### Segment 2: Health Checks & API Verification (0:45 - 1:15)
- **What to show on screen:** Terminal and Swagger UI ([http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)).
- **Action:**
  1. Open terminal and run:
     ```bash
     backend/venv/bin/python scripts/test_llm.py
     ```
  2. Show the instant success: `[✓] SUCCESS! Response received in ~0.8s` extracting structured invoice fields.
  3. Show the `/health/llm` endpoint in Swagger:
     ```json
     {"status": "connected", "provider": "gemini", "model": "gemini-flash-lite-latest", "latency_ms": 780}
     ```
- **Talking points:**
  - *"Here we verify that our LLM service is active and responding with sub-second latency via Google AI Studio."*

---

### Segment 3: Multi-Format Document Ingestion (1:15 - 2:00)
- **What to show on screen:** Web dashboard ([http://localhost:3000](http://localhost:3000)).
- **Action:**
  1. Drag and drop multiple files simultaneously:
     - `inv_acme_cloud.pdf`
     - `ledger_hardware_q1.xlsx`
     - `procurement_march_a.csv`
  2. Click **Upload and Process**.
  3. Show the document table:
     - Status transitions from `QUEUED` ➔ `PROCESSING` ➔ `COMPLETED`.
     - File types: PDF, XLSX, CSV properly identified.
- **Talking points:**
  - *"The ingestion pipeline detects file types via magic bytes and extensions. Uploads return an immediate HTTP 202 Accepted and process asynchronously in the background so the UI never blocks."*

---

### Segment 4: Structured Extraction & Validation Engine (2:00 - 3:00)
- **What to show on screen:** Click on `inv_acme_cloud.pdf` to view the Document Detail view.
- **Action:**
  1. Show the **Extracted Data Form**:
     - Invoice Number (`INV-2026-001`), Date (`2026-01-15`), Supplier (`Acme Cloud Corp`), Total (`$1320.00`).
     - Itemized Line Items table with quantities, prices, and line totals.
     - Confidence score: `1.0`.
  2. Switch to the **Validation Audit Tab**:
     - Explain the deterministic rules: `subtotal + tax == total` (1200 + 120 = 1320).
     - Point out the duplicate invoice check.
- **Talking points:**
  - *"Our system follows a strict zero-hallucination policy. Missing fields are set to null rather than guessed. Then, our deterministic Python validation engine verifies all arithmetic invariants independently of the LLM."*

---

### Segment 5: Human-in-the-Loop Corrections & Audit Trail (3:00 - 3:45)
- **What to show on screen:** Document Detail View -> Extracted Data.
- **Action:**
  1. Edit a field: change `total` to `9999.00` or change the invoice number.
  2. Click **Save Corrections**.
  3. Notice the immediate result:
     - The validation engine instantly detects the arithmetic discrepancy (`subtotal + tax != total`).
     - A red warning/error badge appears: `Validation Error: Subtotal (1200) + Tax (120) != Total (9999)`.
  4. View the **Audit Trail / History Tab**:
     - Shows the exact change logged: field `total`, old value `1320.0`, new value `9999.0`, reviewer ID, and timestamp.
  5. Fix the total back to `1320.00` and save. The validation errors clear!
- **Talking points:**
  - *"When reviewers make corrections, changes are logged in an immutable audit trail and validation rules re-execute instantaneously."*

---

### Segment 6: Cross-Document Reconciliation (3:45 - 4:30)
- **What to show on screen:** Document Detail View -> Click **Cross-Verify**.
- **Action:**
  1. Click **Cross-Verify Document**.
  2. Select a reference document from the dropdown (e.g. an Excel procurement ledger).
  3. Click **Run Reconciliation**:
     - Displays reconciliation comparison: matching invoice numbers, comparing vendor names, and flagging any price variances.
- **Talking points:**
  - *"This eliminates invoice mismatch errors between supplier PDF invoices and internal Excel purchase ledgers."*

---

### Segment 7: Keyword & Vector Search (4:30 - 5:15)
- **What to show on screen:** Navigate to `/search` ([http://localhost:3000/search](http://localhost:3000/search)).
- **Action:**
  1. Search for keyword: `INV-2026-001` or `Acme`. Show instant keyword matches.
  2. Toggle to **Semantic Search**:
     - Search conceptual query: `"cloud hosting and compute services"`.
     - Show how the cosine similarity engine retrieves relevant invoices even without exact keyword matches.
- **Talking points:**
  - *"We support hybrid search: fast B-tree keyword search for exact invoice lookups, and vector embeddings for contextual semantic retrieval."*

---

### Segment 8: Automated Tests & Evaluation Metrics (5:15 - 5:45)
- **What to show on screen:** Terminal.
- **Action:**
  1. Run `make test`:
     - Show: `38 passed in ~2.5s, 72% coverage`.
  2. Show `evaluation/report.md`:
     - Show: `100.0% success rate, 0.913s average latency, 80% field accuracy`.
- **Talking points:**
  - *"We maintain 72% automated test coverage across 38 unit and integration tests. Our empirical evaluation against 15 labeled documents demonstrates a 100% processing success rate with sub-second latency."*

---

### Segment 9: Conclusion (5:45 - 6:00)
- *"Thank you for watching! The full source code, test suite, architecture diagrams, and setup instructions are provided in the repository."*

---

## 3. Submitting the Video

Once recorded:
1. Copy the public share link from Loom / YouTube / Google Drive.
2. Replace the placeholder link at the top of this document:
   ```markdown
   > **Video Link:** `https://www.loom.com/share/your-actual-recording-id](https://drive.google.com/file/d/1ydKOY617EEUGpzvoK7AmOoFbjuO06ZZY/view?usp=drive_link`
   ```
3. Commit and push the updated link to your Git repository.
