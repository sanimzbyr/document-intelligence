# AI-Assisted Development & Prompt Engineering Disclosure

## 1. Disclosure of AI Assistance
In accordance with modern engineering standards and project deliverable requirements, this document outlines how AI capabilities and prompt engineering were integrated into both the application runtime and the development process.

---

## 2. Production AI Prompts

The production system stores all LLM prompt templates in dedicated files under `backend/app/prompts/` to ensure maintainability, version control, and separation of prompt engineering from application code.

### 2.1 Information Extraction Prompt (`backend/app/prompts/extraction_prompt.txt`)
- **Role:** Extracts structured invoice data from parsed documents into strict JSON.
- **Key Directives:**
  - Strict enforcement of zero hallucination: if a field is not explicitly present, it must be returned as `null`.
  - Normalization of dates to ISO-8601 (`YYYY-MM-DD`).
  - Standardized 3-letter currency codes (`USD`, `EUR`, `GBP`).
  - Itemized extraction of line items with description, quantity, unit price, and total amount.
  - Overall extraction confidence score (0.0 to 1.0) and observations recorded in a `notes` field.

### 2.2 Semantic Audit Prompt (`backend/app/prompts/validation_prompt.txt`)
- **Role:** Performs contextual audit checks on unusual invoices or suspicious supplier descriptions.

---

## 3. Grounding and Hallucination Prevention Measures

1. **Schema Validation via Pydantic:**
   All LLM responses are parsed and validated through the `ExtractedInvoiceData` Pydantic model. If an LLM returns extraneous keys or malformed structures, the system sanitizes the payload.
2. **Deterministic Arithmetic Boundary:**
   Calculations (`subtotal + tax == total`, `sum(line_items) == subtotal`) are executed in Python code, completely isolated from LLM output.
3. **Fallback Heuristic Parser:**
   When an API key is missing or offline, the system utilizes deterministic regex and table-parsing logic rather than guessing or failing silently.
