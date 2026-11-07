"""
AI Information Extraction Service.
Extracts structured invoice JSON using Free LLM APIs (Google Gemini, Groq, OpenRouter, Ollama)
or OpenAI, with fallback deterministic parsing.
Adheres strictly to the rule: Never hallucinate or invent missing fields.
"""
import os
import re
import json
import asyncio
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.document import ExtractedInvoiceData, LineItem
from app.utils.logger import logger


class ExtractionService:
    def __init__(self):
        self.prompt_template = self._load_prompt()
        self.client: Optional[AsyncOpenAI] = None
        
        provider, api_key, base_url, model = settings.get_llm_credentials()
        self.provider = provider
        self.model = model
        
        # Valid active key check
        if api_key and api_key not in ("mock-or-real-api-key", "your-openai-api-key-here", "your-gemini-api-key-here", "your-groq-api-key-here"):
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = AsyncOpenAI(**client_kwargs)
            logger.info(f"Initialized LLM client for provider: {self.provider} (model: {self.model})")

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "extraction_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Extract structured invoice JSON: invoice_number, invoice_date, supplier_name, customer_name, subtotal, tax, total, currency, line_items."

    async def extract_information(self, text: str) -> ExtractedInvoiceData:
        """
        Extract structured financial data from document text.
        Retries up to 3 times with exponential backoff on transient errors.
        """
        if not text or not text.strip():
            logger.warning("Empty text supplied for extraction.")
            return ExtractedInvoiceData(
                confidence=0.0,
                notes="Document contained no extractable text."
            )

        max_chars = 25000
        analysis_text = text[:max_chars] if len(text) > max_chars else text

        if self.client:
            prompt = self.prompt_template.replace("{document_text}", analysis_text)
            for attempt in range(1, 4):
                try:
                    kwargs = {
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a specialized financial information extraction system. Return strictly valid JSON adhering to the user's schema."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.0
                    }
                    # Include json response format where supported
                    if self.provider in ("openai", "groq", "gemini"):
                        kwargs["response_format"] = {"type": "json_object"}

                    response = await self.client.chat.completions.create(**kwargs)
                    content = response.choices[0].message.content
                    
                    # Clean markdown code block fences if returned by model
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()

                    data = json.loads(content)
                    return self._clean_and_validate(data, raw_response=content)
                except Exception as e:
                    logger.warning(f"LLM extraction attempt {attempt} failed ({self.provider}): {e}")
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.error(f"All LLM extraction attempts failed, falling back to heuristic extraction: {e}")

        # Fallback heuristic / deterministic extractor
        return self._heuristic_fallback_extraction(text)

    def _clean_and_validate(self, data: Dict[str, Any], raw_response: Optional[str] = None) -> ExtractedInvoiceData:
        """Sanitize raw LLM JSON output through Pydantic model."""
        line_items_raw = data.get("line_items", [])
        line_items = []
        if isinstance(line_items_raw, list):
            for item in line_items_raw:
                if isinstance(item, dict) and item.get("description"):
                    line_items.append(LineItem(
                        description=str(item.get("description")),
                        quantity=self._safe_float(item.get("quantity")),
                        unit_price=self._safe_float(item.get("unit_price")),
                        amount=self._safe_float(item.get("amount"))
                    ))

        confidence = self._safe_float(data.get("confidence"))
        if confidence is None or confidence < 0.0 or confidence > 1.0:
            confidence = 0.90

        return ExtractedInvoiceData(
            invoice_number=str(data["invoice_number"]).strip() if data.get("invoice_number") else None,
            invoice_date=str(data["invoice_date"]).strip() if data.get("invoice_date") else None,
            supplier_name=str(data["supplier_name"]).strip() if data.get("supplier_name") else None,
            customer_name=str(data["customer_name"]).strip() if data.get("customer_name") else None,
            subtotal=self._safe_float(data.get("subtotal")),
            tax=self._safe_float(data.get("tax")),
            total=self._safe_float(data.get("total")),
            currency=str(data["currency"]).strip().upper() if data.get("currency") else None,
            line_items=line_items,
            confidence=confidence,
            notes=data.get("notes") or (f"Extracted via {self.provider} ({self.model})." if raw_response else None)
        )

    def _heuristic_fallback_extraction(self, text: str) -> ExtractedInvoiceData:
        """
        Deterministic regex and pattern based extraction.
        Ensures system functions reliably even without an active API key.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # 1. Invoice Number (match explicit labels with word boundaries)
        invoice_number = None
        inv_patterns = [
            r"\b(?:invoice\s*(?:no|number|num)\.?|invoice\s*#|inv\s*#)\s*[:.\s-]*([A-Za-z0-9-_/]+)",
            r"\binvoice\s*[:\s-]\s*#?\s*([A-Za-z0-9-_/]+)",
            r"\brec(?:eipt)?\s*#\s*[:.\s-]*([A-Za-z0-9-_/]+)"
        ]
        for pat in inv_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if candidate.lower() not in ("date", "due", "currency", "total", "subtotal", "to", "number", "no", "invoice", "rec", "supplier"):
                    invoice_number = candidate
                    break

        # Check for tabular CSV/Excel layout
        if not invoice_number:
            tab_match = re.search(r"Invoice\s*Number.*?\n\s*([A-Za-z0-9-_/]+)", text, re.IGNORECASE)
            if tab_match:
                candidate = tab_match.group(1).strip()
                if candidate.lower() not in ("supplier", "date", "customer"):
                    invoice_number = candidate

        # 2. Invoice Date
        date_match = re.search(
            r"\b(?:date|invoice\s*date)\s*[:.\s-]*([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}|[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}|[A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})",
            text,
            re.IGNORECASE
        )
        invoice_date = date_match.group(1).strip() if date_match else None

        # 3. Currency
        currency = None
        if "$" in text or "USD" in text.upper():
            currency = "USD"
        elif "€" in text or "EUR" in text.upper():
            currency = "EUR"
        elif "£" in text or "GBP" in text.upper():
            currency = "GBP"

        # 4. Supplier Name
        supplier_name = None
        for line in lines[:5]:
            if not re.search(r"invoice|bill\s*to|receipt|date|#|page|payment", line, re.IGNORECASE) and len(line) > 3:
                supplier_name = line
                break

        # 5. Customer Name
        customer_name = None
        bill_to_match = re.search(r"(?:bill\s*to|customer|client|sold\s*to)\s*[:.\s-]*([A-Za-z0-9\s.,]+)", text, re.IGNORECASE)
        if bill_to_match:
            customer_name = bill_to_match.group(1).split("\n")[0].strip()

        # 6. Totals
        subtotal = None
        tax = None
        total = None

        sub_match = re.search(r"\bsubtotal\s*[:.\s-]*[$€£]?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
        if sub_match:
            subtotal = self._safe_float(sub_match.group(1).replace(",", ""))

        tax_match = re.search(r"\b(?:tax|vat)(?:\s*\([0-9%]+\))?\s*[:.\s-]*[$€£]?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
        if tax_match:
            tax = self._safe_float(tax_match.group(1).replace(",", ""))

        tot_match = re.search(r"\b(?:grand\s*total|total\s*amount|total|received|amount\s*paid)\s*[:.\s-]*[$€£]?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
        if tot_match:
            total = self._safe_float(tot_match.group(1).replace(",", ""))

        # Tabular extraction for totals & fields if Excel/CSV table detected
        if "Invoice Number" in text or "invoice_number" in text:
            for line in lines:
                row_match_a = re.search(r"\b(INV-[A-Za-z0-9-_/]+)\s+(.*?)\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\s+(.*?)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([A-Z]{3})", line)
                if row_match_a:
                    invoice_number = row_match_a.group(1)
                    supplier_name = row_match_a.group(2).strip()
                    invoice_date = row_match_a.group(3)
                    customer_name = row_match_a.group(4).strip()
                    subtotal = self._safe_float(row_match_a.group(5))
                    tax = self._safe_float(row_match_a.group(6))
                    total = self._safe_float(row_match_a.group(7))
                    currency = row_match_a.group(8)
                    break
                parts = [p.strip() for p in re.split(r"\s{2,}|\t|,", line) if p.strip()]
                if len(parts) >= 6 and any(p.startswith("INV-") for p in parts):
                    for p in parts:
                        if p.startswith("INV-"):
                            invoice_number = p
                            break
                    for p in parts:
                        if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", p):
                            invoice_date = p
                            break
                    num_parts = [self._safe_float(p) for p in parts if re.match(r"^[0-9.]+$", p)]
                    num_parts = [n for n in num_parts if n is not None]
                    if len(num_parts) >= 3:
                        subtotal = num_parts[0]
                        tax = num_parts[1]
                        total = num_parts[2]
                    for p in parts:
                        if p in ("USD", "EUR", "GBP"):
                            currency = p
                            break

        # 7. Line items heuristic
        line_items = []
        for line in lines:
            line_match = re.search(r"^(.*?)\s+([0-9]+(?:\.[0-9]+)?)\s+[$€£]?([0-9]+\.[0-9]{2})\s+[$€£]?([0-9]+\.[0-9]{2})$", line)
            if line_match:
                desc = line_match.group(1).strip()
                qty = self._safe_float(line_match.group(2))
                price = self._safe_float(line_match.group(3))
                amount = self._safe_float(line_match.group(4))
                if desc and not re.search(r"description|item|quantity|subtotal|total|tax", desc, re.IGNORECASE):
                    line_items.append(LineItem(description=desc, quantity=qty, unit_price=price, amount=amount))

        confidence = 0.90 if (invoice_number and total) else 0.50

        return ExtractedInvoiceData(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name=supplier_name,
            customer_name=customer_name,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=currency,
            line_items=line_items,
            confidence=confidence,
            notes="Extracted using deterministic pattern parser."
        )

    def _safe_float(self, val: Any) -> Optional[float]:
        if val is None or val == "":
            return None
        try:
            cleaned = str(val).replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()
            return round(float(cleaned), 2)
        except (ValueError, TypeError):
            return None


extraction_service = ExtractionService()
