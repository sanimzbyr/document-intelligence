"""
Unit tests for text extraction pipelines across formats.
"""
import os
import pytest
import pandas as pd
from app.pipelines.text_extractor import text_extractor
from scripts.seed_demo import generate_sample_pdf, generate_sample_excel, generate_sample_csv


def test_pdf_extraction(tmp_path):
    pdf_path = str(tmp_path / "test_invoice.pdf")
    generate_sample_pdf(pdf_path)

    pages = text_extractor.extract(pdf_path, "pdf")
    assert len(pages) == 1
    assert "Acme Cloud Solutions Inc." in pages[0]["text"]
    assert "INV-2026-0042" in pages[0]["text"]
    assert "$2145.00" in pages[0]["text"]


def test_excel_extraction(tmp_path):
    excel_path = str(tmp_path / "test_ledger.xlsx")
    generate_sample_excel(excel_path)

    pages = text_extractor.extract(excel_path, "xlsx")
    assert len(pages) == 2  # Two sheets
    assert "Sheet: Invoice Ledger" in pages[0]["text"]
    assert "INV-2026-0042" in pages[0]["text"]
    assert "Sheet: Budget Summary" in pages[1]["text"]


def test_csv_extraction(tmp_path):
    csv_path = str(tmp_path / "test_data.csv")
    generate_sample_csv(csv_path)

    pages = text_extractor.extract(csv_path, "csv")
    assert len(pages) == 1
    assert "Apex Office Supplies" in pages[0]["text"]
    assert "INV-9921" in pages[0]["text"]


def test_corrupt_file_handling(tmp_path):
    corrupt_pdf = str(tmp_path / "corrupt.pdf")
    with open(corrupt_pdf, "wb") as f:
        f.write(b"NOT A REAL PDF FILE HEADER OR BYTES")

    with pytest.raises(ValueError, match="Corrupt or invalid PDF file"):
        text_extractor.extract(corrupt_pdf, "pdf")


def test_empty_file_handling(tmp_path):
    empty_file = str(tmp_path / "empty.pdf")
    with open(empty_file, "wb") as f:
        pass

    with pytest.raises(ValueError, match="File is empty"):
        text_extractor.extract(empty_file, "pdf")
