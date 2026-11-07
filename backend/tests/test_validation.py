"""
Unit tests for financial validation rules and cross-verification.
"""
import pytest
from app.services.validation_service import validation_service
from app.schemas.document import ExtractedInvoiceData, LineItem


@pytest.mark.asyncio
async def test_validation_valid_invoice():
    data = ExtractedInvoiceData(
        invoice_number="INV-100",
        invoice_date="2026-05-01",
        supplier_name="Valid Supplier Corp",
        subtotal=100.0,
        tax=10.0,
        total=110.0,
        currency="USD",
        line_items=[
            LineItem(description="Service A", quantity=1, unit_price=100.0, amount=100.0)
        ],
        confidence=0.95
    )

    errors, needs_review = await validation_service.validate_document_data("doc_1", data)
    assert len(errors) == 0
    assert needs_review is False


@pytest.mark.asyncio
async def test_validation_missing_required_fields():
    data = ExtractedInvoiceData(
        invoice_number=None,
        invoice_date=None,
        total=None,
        currency=None
    )

    errors, needs_review = await validation_service.validate_document_data("doc_2", data)
    assert needs_review is True
    error_fields = [e["field"] for e in errors]
    assert "invoice_number" in error_fields
    assert "invoice_date" in error_fields
    assert "total" in error_fields


@pytest.mark.asyncio
async def test_validation_math_inconsistency():
    data = ExtractedInvoiceData(
        invoice_number="INV-200",
        invoice_date="2026-05-01",
        subtotal=100.0,
        tax=15.0,
        total=150.0,  # 100 + 15 != 150
        currency="USD"
    )

    errors, needs_review = await validation_service.validate_document_data("doc_3", data)
    assert needs_review is True
    math_errors = [e for e in errors if "Mathematical inconsistency" in e["message"]]
    assert len(math_errors) == 1


@pytest.mark.asyncio
async def test_validation_line_items_mismatch():
    data = ExtractedInvoiceData(
        invoice_number="INV-300",
        invoice_date="2026-05-01",
        subtotal=200.0,
        tax=0.0,
        total=200.0,
        currency="USD",
        line_items=[
            LineItem(description="Widget", quantity=2, unit_price=50.0, amount=80.0)  # 2 * 50 != 80, sum != 200
        ]
    )

    errors, needs_review = await validation_service.validate_document_data("doc_4", data)
    assert needs_review is True
    assert any("recorded amount is 80.0" in e["message"] for e in errors)
    assert any("Sum of line items" in e["message"] for e in errors)


def test_cross_verification_matching():
    data_a = ExtractedInvoiceData(
        invoice_number="INV-888",
        supplier_name="Global Tech Ltd",
        total=500.0
    )
    data_b = ExtractedInvoiceData(
        invoice_number="INV-888",
        supplier_name="Global Tech Ltd",
        total=500.0
    )

    res = validation_service.cross_verify_documents("doc_a.pdf", data_a, "doc_b.xlsx", data_b)
    assert res.is_match is True
    assert res.confidence == 1.0


def test_cross_verification_mismatch():
    data_a = ExtractedInvoiceData(
        invoice_number="INV-888",
        supplier_name="Global Tech Ltd",
        total=500.0
    )
    data_b = ExtractedInvoiceData(
        invoice_number="INV-999",
        supplier_name="Different Supplier",
        total=650.0
    )

    res = validation_service.cross_verify_documents("doc_a.pdf", data_a, "doc_b.xlsx", data_b)
    assert res.is_match is False
    assert len([d for d in res.discrepancies if d.status == "MISMATCH"]) >= 2
