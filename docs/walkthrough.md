# Video Walkthrough Script & Demo Guide

This document provides a structured walkthrough script for reviewing or recording a demonstration video of the **AI-Powered Document Intelligence System**.

> **Demo Video Link Placeholder:**  
> `https://www.loom.com/share/placeholder-docu-intelligence-walkthrough`

---

## Demo Script Flow (Duration: ~4-5 Minutes)

### Part 1: Architecture & System Startup (0:00 - 0:45)
1. **Show the codebase structure:**
   - FastAPI backend (`backend/app`), Next.js 14 frontend (`frontend/app`), evaluation benchmark (`evaluation/`), and documentation (`docs/`).
2. **Start the application:**
   - Execute `docker compose up` or run `make dev` and `npm run dev` in the frontend directory.
   - Show health check response at `http://localhost:8000/health`.

### Part 2: Batch Document Ingestion (0:45 - 1:45)
1. Navigate to the web frontend at `http://localhost:3000`.
2. Demonstrate multi-file drag and drop using a mixed batch:
   - A digital PDF invoice (`demo_acme_invoice.pdf`).
   - A multi-sheet Excel spreadsheet (`demo_ledger_q1.xlsx`).
   - A CSV procurement ledger (`demo_procurement.csv`).
   - A scanned receipt image (`demo_receipt.png`).
3. Point out:
   - File size validation and supported format filtering.
   - Status transitions from `Queued` to `Processing` with animated progress polling.
   - Immediate non-blocking response.

### Part 3: AI Information Extraction & Validation Audit (1:45 - 2:45)
1. Open the processed PDF invoice (`demo_acme_invoice.pdf`).
2. Review the **Extracted Data Tab**:
   - Invoice number, date, supplier, customer, subtotal, tax, total, currency, and itemized line items.
   - Confidence score and model observations.
3. Review the **Validation Errors Tab**:
   - Highlight the arithmetic checks: `subtotal + tax == total` and line item sum comparisons.
   - Explain how any inconsistency automatically flags `needs_review = true`.

### Part 4: Manual Human Correction & Live Audit Trail (2:45 - 3:30)
1. Modify one of the extracted fields (e.g., adjust the invoice number or line item price).
2. Click **Save Corrections**.
3. Point out:
   - The validation rules immediately re-run in real-time.
   - The **Audit & History Tab** logs the modification: old value, new value, timestamp, and user identifier.

### Part 5: Cross-Document Reconciliation (3:30 - 4:15)
1. Click the **Cross-Verify** button.
2. Select the matching Excel ledger file (`demo_ledger_q1.xlsx`).
3. Click **Run Cross-Verification**:
   - Show how the system compares the PDF invoice against the Excel spreadsheet record.
   - Display the reconciliation status: matched fields vs. discrepancies.

### Part 6: Keyword & Semantic Vector Search (4:15 - 4:45)
1. Navigate to the **Search & Intelligence** page (`/search`).
2. Demonstrate **Keyword Search**:
   - Query exact invoice number: `INV-2026-0042`.
3. Demonstrate **Semantic Search**:
   - Toggle to "Semantic Search" and query conceptual phrases like *"cloud hosting and infrastructure"*.
   - Show matching documents retrieved via OpenAI vector embeddings and cosine similarity.

### Part 7: Automated Tests & Evaluation Metrics (4:45 - 5:00)
1. Run `make test` showing 35 unit/integration tests passing with >70% coverage.
2. Run `make eval` showing the empirical benchmark generating `evaluation/report.md` with 100% document success rate.
