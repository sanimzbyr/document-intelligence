"""
Document, extraction, validation, and history Pydantic schemas.
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class LineItem(BaseModel):
    description: str = Field(..., description="Description of the item or service")
    quantity: Optional[float] = Field(None, description="Quantity purchased")
    unit_price: Optional[float] = Field(None, description="Unit price per item")
    amount: Optional[float] = Field(None, description="Total amount for the line item")


class ExtractedInvoiceData(BaseModel):
    """Schema for LLM structured output and stored extracted data."""
    invoice_number: Optional[str] = Field(None, description="Invoice or reference number")
    invoice_date: Optional[str] = Field(None, description="Invoice date in ISO format YYYY-MM-DD if possible")
    supplier_name: Optional[str] = Field(None, description="Vendor or supplier company name")
    customer_name: Optional[str] = Field(None, description="Buyer or recipient name")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax: Optional[float] = Field(None, description="Tax or VAT amount")
    total: Optional[float] = Field(None, description="Grand total amount")
    currency: Optional[str] = Field(None, description="Currency symbol or code (e.g. USD, EUR, $)")
    line_items: List[LineItem] = Field(default_factory=list, description="List of itemized products or services")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    notes: Optional[str] = Field(None, description="Observations, uncertainties, or missing fields")


class ExtractedDataUpdate(BaseModel):
    """Schema for manual corrections via PATCH."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    supplier_name: Optional[str] = None
    customer_name: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    currency: Optional[str] = None
    line_items: Optional[List[LineItem]] = None
    notes: Optional[str] = None


class ValidationErrorSchema(BaseModel):
    id: str
    field: str
    severity: str  # error, warning
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CorrectionHistorySchema(BaseModel):
    id: str
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    corrected_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingHistorySchema(BaseModel):
    id: str
    stage: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedTextSchema(BaseModel):
    id: str
    page_number: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    page_count: int
    needs_review: bool
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    extracted_data: Optional[ExtractedInvoiceData] = None
    extracted_text: List[ExtractedTextSchema] = []
    validation_errors: List[ValidationErrorSchema] = []
    correction_history: List[CorrectionHistorySchema] = []
    processing_history: List[ProcessingHistorySchema] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    progress: int  # 0 to 100
    current_stage: Optional[str] = None
    needs_review: bool
    error_message: Optional[str] = None


class BatchUploadResponse(BaseModel):
    uploaded: List[DocumentResponse]
    failed: List[Dict[str, str]]


class CrossVerificationRequest(BaseModel):
    primary_document_id: str
    reference_document_id: str


class CrossVerificationDiscrepancy(BaseModel):
    field: str
    primary_value: Any
    reference_value: Any
    status: str  # MATCH, MISMATCH, MISSING
    message: str


class CrossVerificationResponse(BaseModel):
    is_match: bool
    confidence: float
    discrepancies: List[CrossVerificationDiscrepancy]
    summary: str
