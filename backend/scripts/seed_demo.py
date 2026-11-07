"""
Database seeding and synthetic document generation script.
Generates sample PDF, Excel, CSV, and Image files, and seeds the database with demo documents.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import (
    User,
    Document,
    ExtractedText,
    ExtractedData,
    ValidationError,
    ProcessingHistory,
)
from app.pipelines.orchestrator import pipeline_orchestrator
from app.utils.logger import logger


def generate_sample_pdf(filepath: str):
    """Generate a clean synthetic invoice PDF using ReportLab."""
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 60, "Acme Cloud Solutions Inc.")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 75, "100 Innovation Way, Suite 400, San Francisco, CA")
    c.drawString(50, height - 90, "Email: billing@acmecloud.com | Phone: (555) 019-2834")

    # Invoice Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, height - 60, "INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(400, height - 75, "Invoice #: INV-2026-0042")
    c.drawString(400, height - 90, "Invoice Date: 2026-03-15")
    c.drawString(400, height - 105, "Due Date: 2026-04-15")
    c.drawString(400, height - 120, "Currency: USD")

    # Bill To
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 140, "Bill To:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 155, "Global Enterprises LLC")
    c.drawString(50, height - 170, "Attn: Accounts Payable")
    c.drawString(50, height - 185, "500 Market St, Denver, CO")

    # Table Header
    y = height - 220
    c.line(50, y + 15, 550, y + 15)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Item Description")
    c.drawString(320, y, "Qty")
    c.drawString(380, y, "Unit Price")
    c.drawString(480, y, "Amount")
    c.line(50, y - 5, 550, y - 5)

    # Line Items
    items = [
        ("Cloud Infrastructure - Enterprise Plan", "1", "1200.00", "1200.00"),
        ("Dedicated IP & VPN Gateway", "2", "150.00", "300.00"),
        ("Priority 24/7 Technical Support", "1", "450.00", "450.00"),
    ]

    c.setFont("Helvetica", 10)
    y -= 25
    for desc, qty, price, amt in items:
        c.drawString(50, y, desc)
        c.drawString(325, y, qty)
        c.drawString(385, y, f"${price}")
        c.drawString(485, y, f"${amt}")
        y -= 20

    c.line(50, y + 5, 550, y + 5)

    # Summary Totals
    y -= 15
    c.drawString(380, y, "Subtotal:")
    c.drawString(485, y, "$1950.00")
    y -= 18
    c.drawString(380, y, "Tax (10%):")
    c.drawString(485, y, "$195.00")
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(380, y, "Total Amount:")
    c.drawString(485, y, "$2145.00")

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 60, "Thank you for your business. Please remit payment within 30 days.")
    c.save()


def generate_sample_excel(filepath: str):
    """Generate a multi-sheet financial spreadsheet."""
    sheet1_data = {
        "Invoice Number": ["INV-2026-0042", "INV-2026-0089", "INV-2026-0105"],
        "Supplier": ["Acme Cloud Solutions Inc.", "Starlight Logistics", "Nordic Data Systems"],
        "Invoice Date": ["2026-03-15", "2026-03-18", "2026-03-22"],
        "Subtotal": [1950.00, 3400.00, 890.50],
        "Tax": [195.00, 340.00, 89.05],
        "Total Amount": [2145.00, 3740.00, 979.55],
        "Currency": ["USD", "USD", "EUR"],
        "Status": ["Verified", "Pending Review", "Verified"]
    }
    sheet2_data = {
        "Department": ["Engineering", "Logistics", "Operations"],
        "Budget Allocated": [50000.00, 25000.00, 15000.00],
        "YTD Spend": [31450.00, 18900.00, 11200.00]
    }
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        pd.DataFrame(sheet1_data).to_excel(writer, sheet_name="Invoice Ledger", index=False)
        pd.DataFrame(sheet2_data).to_excel(writer, sheet_name="Budget Summary", index=False)


def generate_sample_csv(filepath: str):
    """Generate a CSV invoice ledger."""
    data = {
        "invoice_number": ["INV-9921", "INV-9922", "INV-9923"],
        "invoice_date": ["2026-04-01", "2026-04-02", "2026-04-05"],
        "supplier_name": ["Apex Office Supplies", "Vertex Power Corp", "Zenith Telecom"],
        "customer_name": ["Global Enterprises LLC", "Global Enterprises LLC", "Global Enterprises LLC"],
        "subtotal": [450.00, 1250.00, 320.00],
        "tax": [45.00, 125.00, 32.00],
        "total": [495.00, 1375.00, 352.00],
        "currency": ["USD", "USD", "USD"]
    }
    pd.DataFrame(data).to_csv(filepath, index=False)


def generate_sample_image(filepath: str):
    """Generate a clean synthetic receipt image."""
    img = Image.new("RGB", (700, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        "METRO LOGISTICS SERVICES",
        "123 Delivery Road, Chicago, IL",
        "Phone: 312-555-0199",
        "------------------------------------",
        "INVOICE #: REC-88310",
        "DATE: 2026-04-10",
        "CUSTOMER: Global Enterprises LLC",
        "------------------------------------",
        "Freight Shipping (Expedited)   $350.00",
        "Fuel Surcharge                  $35.00",
        "Handling & Packaging            $25.00",
        "------------------------------------",
        "SUBTOTAL:                      $410.00",
        "TAX:                            $41.00",
        "TOTAL:                         $451.00",
        "CURRENCY: USD",
        "------------------------------------",
        "STATUS: PAID IN FULL"
    ]

    y = 30
    for line in lines:
        draw.text((40, y), line, fill=(0, 0, 0))
        y += 24

    img.save(filepath)


async def seed():
    """Main database seeding routine."""
    logger.info("Initializing tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Create Demo Admin User
        admin_email = "admin@company.com"
        stmt = select(User).where(User.email == admin_email)
        existing_user = (await session.execute(stmt)).scalars().first()
        if not existing_user:
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123")
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            user_id = admin_user.id
            logger.info("Created default admin user: admin@company.com / admin123")
        else:
            user_id = existing_user.id

        # 2. Generate Synthetic Documents
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        pdf_path = os.path.join(settings.STORAGE_DIR, "demo_acme_invoice.pdf")
        xlsx_path = os.path.join(settings.STORAGE_DIR, "demo_ledger_q1.xlsx")
        csv_path = os.path.join(settings.STORAGE_DIR, "demo_procurement.csv")
        png_path = os.path.join(settings.STORAGE_DIR, "demo_receipt.png")

        generate_sample_pdf(pdf_path)
        generate_sample_excel(xlsx_path)
        generate_sample_csv(csv_path)
        generate_sample_image(png_path)
        logger.info("Generated sample files in storage directory.")

        # 3. Create Documents and run through pipeline
        sample_files = [
            ("demo_acme_invoice.pdf", "pdf", pdf_path),
            ("demo_ledger_q1.xlsx", "xlsx", xlsx_path),
            ("demo_procurement.csv", "csv", csv_path),
            ("demo_receipt.png", "png", png_path),
        ]

        for filename, ftype, path in sample_files:
            stmt = select(Document).where(Document.filename == filename)
            existing_doc = (await session.execute(stmt)).scalars().first()
            if not existing_doc:
                doc = Document(
                    user_id=user_id,
                    filename=filename,
                    file_type=ftype,
                    file_path=path,
                    status="queued",
                    page_count=1
                )
                session.add(doc)
                await session.commit()
                await session.refresh(doc)
                
                # Run pipeline directly
                logger.info(f"Processing seeded document: {filename}")
                await pipeline_orchestrator.process_document(doc.id, db=session)
                await session.commit()

        logger.info("Demo data seeding completed successfully!")


if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(seed())
