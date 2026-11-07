"""
Unit tests for AI information extraction and fallback parsers.
"""
import pytest
from app.services.extraction_service import extraction_service


@pytest.mark.asyncio
async def test_extraction_empty_text():
    res = await extraction_service.extract_information("")
    assert res.confidence == 0.0
    assert "no extractable text" in res.notes.lower()


@pytest.mark.asyncio
async def test_extraction_heuristic_standard_invoice():
    text = """
    ACME CORPORATION
    123 Main Street, New York, NY
    
    INVOICE
    Invoice Number: INV-7721
    Invoice Date: 2026-02-14
    Bill To: Tech Vanguard LLC
    
    Item Description               Qty    Unit Price    Amount
    Software Consulting Services     2       150.00     300.00
    Server Maintenance               1       100.00     100.00
    
    Subtotal: $400.00
    Tax: $40.00
    Total: $440.00
    Currency: USD
    """
    res = await extraction_service.extract_information(text)
    assert res.invoice_number == "INV-7721"
    assert res.invoice_date == "2026-02-14"
    assert res.subtotal == 400.0
    assert res.tax == 40.0
    assert res.total == 440.0
    assert res.currency == "USD"
    assert len(res.line_items) == 2


@pytest.mark.asyncio
async def test_extraction_missing_fields_no_hallucination():
    text = """
    Payment Receipt
    Received $50.00 for office lunch.
    Thank you!
    """
    res = await extraction_service.extract_information(text)
    assert res.invoice_number is None  # Never hallucinate an invoice number
    assert res.subtotal is None
    assert res.total == 50.0
