"""
SQLAlchemy ORM models.
Defines schemas for Users, Documents, Extracted Text, Extracted Data,
Validation Errors, Correction History, and Processing History.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(50), default="queued", nullable=False, index=True)  # queued, processing, completed, failed
    page_count = Column(Integer, default=1, nullable=False)
    error_message = Column(Text, nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="documents")
    extracted_text = relationship("ExtractedText", back_populates="document", cascade="all, delete-orphan")
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False, cascade="all, delete-orphan")
    validation_errors = relationship("ValidationError", back_populates="document", cascade="all, delete-orphan")
    correction_history = relationship("CorrectionHistory", back_populates="document", cascade="all, delete-orphan")
    processing_history = relationship("ProcessingHistory", back_populates="document", cascade="all, delete-orphan")


class ExtractedText(Base):
    __tablename__ = "extracted_text"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, default=1)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector representation stored as list of floats
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="extracted_text")


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_date = Column(String(50), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    line_items = Column(JSON, default=list, nullable=False)  # List of {description, quantity, unit_price, amount}
    confidence = Column(Float, default=1.0, nullable=False)
    notes = Column(Text, nullable=True)
    raw_llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    document = relationship("Document", back_populates="extracted_data")


class ValidationError(Base):
    __tablename__ = "validation_errors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # error, warning
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="validation_errors")


class CorrectionHistory(Base):
    __tablename__ = "correction_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    corrected_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="correction_history")


class ProcessingHistory(Base):
    __tablename__ = "processing_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(100), nullable=False)  # ingestion, text_extraction, ai_extraction, validation
    status = Column(String(50), nullable=False)  # started, completed, failed
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

    document = relationship("Document", back_populates="processing_history")


# Ensure composite index for duplicate invoice detection
Index("idx_supplier_invoice", ExtractedData.supplier_name, ExtractedData.invoice_number)
