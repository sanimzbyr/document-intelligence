"""
Unit tests for file type detection and sanitization utilities.
"""
from app.utils.file_detection import detect_file_type, sanitize_filename


def test_pdf_magic_byte_detection():
    pdf_bytes = b"%PDF-1.4\n%some binary data"
    is_valid, mime, ext = detect_file_type(pdf_bytes, "invoice.pdf")
    assert is_valid is True
    assert mime == "application/pdf"
    assert ext == ".pdf"


def test_png_magic_byte_detection():
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    is_valid, mime, ext = detect_file_type(png_bytes, "scan.png")
    assert is_valid is True
    assert mime == "image/png"
    assert ext == ".png"


def test_jpeg_magic_byte_detection():
    jpg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    is_valid, mime, ext = detect_file_type(jpg_bytes, "receipt.jpg")
    assert is_valid is True
    assert mime == "image/jpeg"
    assert ext == ".jpg"


def test_csv_detection():
    csv_bytes = b"invoice_number,date,total\nINV-001,2026-01-01,100.00"
    is_valid, mime, ext = detect_file_type(csv_bytes, "data.csv")
    assert is_valid is True
    assert mime == "text/csv"
    assert ext == ".csv"


def test_invalid_file_rejection():
    exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00"
    is_valid, mime, ext = detect_file_type(exe_bytes, "malware.exe")
    assert is_valid is False


def test_filename_sanitization():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("my invoice #1 (2026).pdf") == "myinvoice12026.pdf"
    assert sanitize_filename("valid-name_01.xlsx") == "valid-name_01.xlsx"
