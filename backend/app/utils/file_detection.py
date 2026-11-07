"""
File format and MIME type detection using magic bytes and file extensions.
Validates supported file types: PDF, JPG, PNG, TIFF, XLSX, XLS, CSV.
"""
import os
from typing import Tuple

SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
}

# Known magic byte signatures
MAGIC_SIGNATURES = [
    (b"%PDF-", "application/pdf", ".pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"II*\x00", "image/tiff", ".tiff"),
    (b"MM\x00*", "image/tiff", ".tiff"),
    (b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "application/vnd.ms-excel", ".xls"),
]


def detect_file_type(file_bytes: bytes, filename: str) -> Tuple[bool, str, str]:
    """
    Detect and validate file type using magic bytes with fallback to filename extension.
    
    Returns:
        Tuple of (is_valid: bool, mime_type: str, normalized_extension: str)
    """
    _, ext = os.path.splitext(filename.lower())
    
    # 1. Check magic bytes
    for signature, mime, canonical_ext in MAGIC_SIGNATURES:
        if file_bytes.startswith(signature):
            # XLSX shares zip header with other docx/pptx/zip files
            if canonical_ext == ".xlsx" and ext in [".xlsx", ".xlsm"]:
                return True, mime, ".xlsx"
            return True, mime, canonical_ext
            
    # 2. Check CSV (plain text check)
    if ext == ".csv":
        try:
            # Attempt decoding snippet
            file_bytes[:2048].decode("utf-8")
            return True, "text/csv", ".csv"
        except UnicodeDecodeError:
            try:
                file_bytes[:2048].decode("latin-1")
                return True, "text/csv", ".csv"
            except Exception:
                pass

    # 3. Fallback to extension if valid extension and bytes are non-empty
    if ext in SUPPORTED_EXTENSIONS and len(file_bytes) > 0:
        return True, SUPPORTED_EXTENSIONS[ext], ext
        
    return False, "application/octet-stream", ext


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove unsafe chars."""
    basename = os.path.basename(filename)
    safe_chars = "".join(c for c in basename if c.isalnum() or c in (".", "-", "_"))
    return safe_chars or "document"
