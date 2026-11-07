"""
Data Validation Service.
Implements financial consistency rules, required field checks, duplicate detection,
and cross-document reconciliation (PDF-PDF and PDF-Excel).
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import ExtractedData, Document
from app.schemas.document import (
    ExtractedInvoiceData,
    ValidationErrorSchema,
    CrossVerificationResponse,
    CrossVerificationDiscrepancy,
)
from app.utils.logger import logger

KNOWN_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY", "INR", "$", "€", "£", "¥"}


class ValidationService:
    async def validate_document_data(
        self,
        document_id: str,
        data: ExtractedInvoiceData,
        db: Optional[AsyncSession] = None
    ) -> Tuple[List[Dict[str, str]], bool]:
        """
        Validate extracted invoice data against business rules.
        
        Returns:
            Tuple of (errors: List[dict(field, severity, message)], needs_review: bool)
        """
        errors: List[Dict[str, str]] = []

        # 1. Required fields check
        if not data.invoice_number or not str(data.invoice_number).strip():
            errors.append({
                "field": "invoice_number",
                "severity": "error",
                "message": "Missing required field: Invoice Number."
            })

        if not data.invoice_date or not str(data.invoice_date).strip():
            errors.append({
                "field": "invoice_date",
                "severity": "error",
                "message": "Missing required field: Invoice Date."
            })

        if data.total is None:
            errors.append({
                "field": "total",
                "severity": "error",
                "message": "Missing required field: Total Amount."
            })
        elif data.total < 0:
            errors.append({
                "field": "total",
                "severity": "error",
                "message": f"Negative total amount detected: {data.total}."
            })

        # 2. Math Consistency: subtotal + tax ≈ total (tolerance 0.01)
        if data.subtotal is not None and data.tax is not None and data.total is not None:
            expected_total = round(data.subtotal + data.tax, 2)
            actual_total = round(data.total, 2)
            diff = abs(expected_total - actual_total)
            if diff > 0.02:
                errors.append({
                    "field": "total",
                    "severity": "error",
                    "message": f"Mathematical inconsistency: Subtotal ({data.subtotal}) + Tax ({data.tax}) = {expected_total}, but Total is {actual_total} (diff: {round(diff, 2)})."
                })

        # 3. Line Items Consistency: sum(line_items.amount) ≈ subtotal or total
        if data.line_items and len(data.line_items) > 0:
            item_sum = round(sum(item.amount for item in data.line_items if item.amount is not None), 2)
            
            # Check individual line item arithmetic (quantity * unit_price == amount)
            for idx, item in enumerate(data.line_items):
                if item.quantity is not None and item.unit_price is not None and item.amount is not None:
                    calc_amount = round(item.quantity * item.unit_price, 2)
                    if abs(calc_amount - item.amount) > 0.02:
                        errors.append({
                            "field": f"line_items[{idx}]",
                            "severity": "warning",
                            "message": f"Line item '{item.description}': quantity ({item.quantity}) * unit_price ({item.unit_price}) = {calc_amount}, but recorded amount is {item.amount}."
                        })

            # Check sum against subtotal (or total if tax is 0 or absent)
            comparison_target = data.subtotal if data.subtotal is not None else data.total
            target_name = "Subtotal" if data.subtotal is not None else "Total"
            if comparison_target is not None:
                diff = abs(item_sum - comparison_target)
                if diff > 0.05:
                    errors.append({
                        "field": "line_items",
                        "severity": "warning",
                        "message": f"Sum of line items ({item_sum}) does not match {target_name} ({comparison_target}). Difference: {round(diff, 2)}."
                    })

        # 4. Date format check
        if data.invoice_date:
            parsed_date = self._parse_date(data.invoice_date)
            if not parsed_date:
                errors.append({
                    "field": "invoice_date",
                    "severity": "warning",
                    "message": f"Unrecognized or invalid date format: '{data.invoice_date}'."
                })

        # 5. Currency Check
        if data.currency:
            if data.currency.upper() not in KNOWN_CURRENCIES:
                errors.append({
                    "field": "currency",
                    "severity": "warning",
                    "message": f"Unrecognized currency symbol or code: '{data.currency}'."
                })
        else:
            errors.append({
                "field": "currency",
                "severity": "warning",
                "message": "Currency not specified."
            })

        # 6. Duplicate Invoice Check in Database
        if db and data.invoice_number and data.supplier_name:
            stmt = select(ExtractedData).where(
                and_(
                    ExtractedData.invoice_number == data.invoice_number,
                    ExtractedData.supplier_name == data.supplier_name,
                    ExtractedData.document_id != document_id
                )
            )
            result = await db.execute(stmt)
            existing = result.scalars().first()
            if existing:
                errors.append({
                    "field": "invoice_number",
                    "severity": "error",
                    "message": f"Duplicate invoice detected: Invoice '{data.invoice_number}' for supplier '{data.supplier_name}' already exists in document {existing.document_id}."
                })

        # 7. Confidence Score Check
        if data.confidence < 0.65:
            errors.append({
                "field": "confidence",
                "severity": "warning",
                "message": f"Low extraction confidence score: {round(data.confidence * 100, 1)}%."
            })

        needs_review = len(errors) > 0
        return errors, needs_review

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Attempt to parse common date formats."""
        cleaned = re.sub(r"[^\w\s\-/.,]", "", date_str).strip()
        formats = [
            "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y",
            "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None

    def cross_verify_documents(
        self,
        doc_a_name: str,
        data_a: ExtractedInvoiceData,
        doc_b_name: str,
        data_b: ExtractedInvoiceData
    ) -> CrossVerificationResponse:
        """
        Cross-verify two documents (PDF-to-PDF or PDF-to-Excel) to detect accounting discrepancies.
        """
        discrepancies: List[CrossVerificationDiscrepancy] = []

        # 1. Invoice Number
        if data_a.invoice_number and data_b.invoice_number:
            if data_a.invoice_number.strip().lower() == data_b.invoice_number.strip().lower():
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="invoice_number",
                    primary_value=data_a.invoice_number,
                    reference_value=data_b.invoice_number,
                    status="MATCH",
                    message="Invoice numbers match perfectly."
                ))
            else:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="invoice_number",
                    primary_value=data_a.invoice_number,
                    reference_value=data_b.invoice_number,
                    status="MISMATCH",
                    message=f"Invoice numbers mismatch: '{data_a.invoice_number}' vs '{data_b.invoice_number}'."
                ))

        # 2. Total Amount
        if data_a.total is not None and data_b.total is not None:
            diff = abs(data_a.total - data_b.total)
            if diff <= 0.02:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="total",
                    primary_value=data_a.total,
                    reference_value=data_b.total,
                    status="MATCH",
                    message="Totals reconcile within 0.02 tolerance."
                ))
            else:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="total",
                    primary_value=data_a.total,
                    reference_value=data_b.total,
                    status="MISMATCH",
                    message=f"Total mismatch: {data_a.total} in {doc_a_name} vs {data_b.total} in {doc_b_name} (diff: {round(diff, 2)})."
                ))

        # 3. Supplier Name (fuzzy match)
        if data_a.supplier_name and data_b.supplier_name:
            norm_a = re.sub(r"[^\w]", "", data_a.supplier_name.lower())
            norm_b = re.sub(r"[^\w]", "", data_b.supplier_name.lower())
            if norm_a in norm_b or norm_b in norm_a:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="supplier_name",
                    primary_value=data_a.supplier_name,
                    reference_value=data_b.supplier_name,
                    status="MATCH",
                    message="Supplier names match."
                ))
            else:
                discrepancies.append(CrossVerificationDiscrepancy(
                    field="supplier_name",
                    primary_value=data_a.supplier_name,
                    reference_value=data_b.supplier_name,
                    status="MISMATCH",
                    message=f"Supplier mismatch: '{data_a.supplier_name}' vs '{data_b.supplier_name}'."
                ))

        mismatches = [d for d in discrepancies if d.status == "MISMATCH"]
        is_match = len(mismatches) == 0 and len(discrepancies) > 0
        confidence = 1.0 - (len(mismatches) * 0.35)
        confidence = max(0.1, min(1.0, confidence))

        summary = "All cross-verified fields reconciled successfully." if is_match else f"Found {len(mismatches)} discrepancies between {doc_a_name} and {doc_b_name}."

        return CrossVerificationResponse(
            is_match=is_match,
            confidence=round(confidence, 2),
            discrepancies=discrepancies,
            summary=summary
        )


validation_service = ValidationService()
