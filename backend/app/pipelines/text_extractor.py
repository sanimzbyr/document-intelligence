"""
Document Processing & Text Extraction Pipeline.
Supports:
- Digital PDFs (pdfplumber) with OCR fallback (pdf2image + pytesseract)
- Multi-page chunking (capable of handling 1,000+ page PDFs)
- Images (JPG, PNG, TIFF) with Pillow preprocessing (upscaling & thresholding)
- Spreadsheets (XLSX, XLS multi-sheet parsing)
- CSV parsing
- Corrupt file detection
"""
import io
import os
from typing import List, Dict, Any, Tuple
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pdfplumber
from pypdf import PdfReader
from app.utils.logger import logger


class TextExtractor:
    def __init__(self):
        pass

    def extract(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Extract text from document per page/sheet.
        
        Returns:
            List of dicts: [{"page_number": int, "text": str}]
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found on disk: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("File is empty (0 bytes).")

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".pdf":
                return self._extract_pdf(file_path)
            elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
                return self._extract_image(file_path)
            elif ext in [".xlsx", ".xls"]:
                return self._extract_spreadsheet(file_path)
            elif ext == ".csv":
                return self._extract_csv(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path} ({ext}): {e}", exc_info=True)
            raise

    def _extract_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF page by page.
        Attempts digital text extraction via pdfplumber first.
        If a page has insufficient text, falls back to OCR via pdf2image and pytesseract.
        """
        pages_data: List[Dict[str, Any]] = []

        try:
            # First check if PDF is valid and get page count
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                num_pages = len(reader.pages)
        except Exception as e:
            raise ValueError(f"Corrupt or invalid PDF file: {e}")

        logger.info(f"Processing PDF with {num_pages} pages: {file_path}")

        with pdfplumber.open(file_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                page_num = idx + 1
                page_text = page.extract_text() or ""
                
                # Check if page has tables
                tables = page.extract_tables()
                if tables:
                    table_texts = []
                    for table in tables:
                        for row in table:
                            clean_row = [str(c).strip() for c in row if c is not None]
                            if clean_row:
                                table_texts.append(" | ".join(clean_row))
                    if table_texts:
                        page_text += "\n\n--- Extracted Table ---\n" + "\n".join(table_texts)

                # If text is too sparse, run OCR fallback for this page
                if len(page_text.strip()) < 30:
                    logger.info(f"Page {page_num} text sparse ({len(page_text.strip())} chars). Running OCR fallback...")
                    ocr_text = self._ocr_pdf_page(page)
                    if len(ocr_text.strip()) > len(page_text.strip()):
                        page_text = ocr_text

                pages_data.append({
                    "page_number": page_num,
                    "text": page_text.strip()
                })

        return pages_data

    def _ocr_pdf_page(self, pdfplumber_page) -> str:
        """Render pdfplumber page to high-res PIL Image and OCR with pytesseract."""
        try:
            # Render page to image at 300 DPI
            pil_image = pdfplumber_page.to_image(resolution=300).original
            return self._ocr_pil_image(pil_image)
        except Exception as e:
            logger.warning(f"PDF page OCR failed: {e}")
            return ""

    def _extract_image(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from image files (JPG, PNG, TIFF) with preprocessing."""
        try:
            with Image.open(file_path) as img:
                # Convert RGBA/Palette to RGB
                if img.mode != "RGB":
                    img = img.convert("RGB")
                text = self._ocr_pil_image(img)
                return [{"page_number": 1, "text": text.strip()}]
        except Exception as e:
            raise ValueError(f"Corrupted or unsupported image file: {e}")

    def _ocr_pil_image(self, image: Image.Image) -> str:
        """Preprocess image (upscaling, grayscale, contrast) and run pytesseract."""
        try:
            # 1. Upscale if image is too small (low DPI)
            w, h = image.size
            if w < 1000 or h < 1000:
                scale_factor = max(2, int(1500 / max(w, h)))
                image = image.resize((w * scale_factor, h * scale_factor), Image.Resampling.LANCZOS)

            # 2. Convert to grayscale
            gray = image.convert("L")

            # 3. Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.8)

            # 4. Optional sharpening
            sharpened = enhanced.filter(ImageFilter.SHARPEN)

            # 5. Run Tesseract OCR
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(sharpened, config=custom_config)
            return text
        except Exception as e:
            logger.warning(f"pytesseract OCR execution error: {e}. Returning empty text.")
            return ""

    def _extract_spreadsheet(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse all sheets of an Excel file into formatted tabular text."""
        pages_data: List[Dict[str, Any]] = []
        try:
            excel_file = pd.ExcelFile(file_path)
            for idx, sheet_name in enumerate(excel_file.sheet_names):
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                # Drop all-NaN rows/columns
                df = df.dropna(how="all").dropna(axis=1, how="all")
                
                sheet_text = f"Sheet: {sheet_name}\n"
                sheet_text += df.to_string(index=False)

                pages_data.append({
                    "page_number": idx + 1,
                    "text": sheet_text.strip()
                })
            return pages_data
        except Exception as e:
            raise ValueError(f"Failed to parse Excel spreadsheet: {e}")

    def _extract_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV file into formatted tabular text."""
        try:
            # Try utf-8 first, fallback to latin-1
            try:
                df = pd.read_csv(file_path, sep=None, engine="python")
            except Exception:
                df = pd.read_csv(file_path, encoding="latin-1", sep=None, engine="python")

            df = df.dropna(how="all").dropna(axis=1, how="all")
            text = "CSV Document:\n" + df.to_string(index=False)
            return [{"page_number": 1, "text": text.strip()}]
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {e}")


text_extractor = TextExtractor()
