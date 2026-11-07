"""
Document management and processing API endpoints.
"""
import os
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.core.config import settings
from app.core.database import get_db
from app.api.v1.auth import get_current_user_optional, User
from app.models.models import (
    Document,
    ExtractedData,
    ExtractedText,
    ValidationError,
    CorrectionHistory,
    ProcessingHistory,
)
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    BatchUploadResponse,
    ExtractedInvoiceData,
    ExtractedDataUpdate,
    ValidationErrorSchema,
    CorrectionHistorySchema,
    ProcessingHistorySchema,
    ExtractedTextSchema,
    LineItem,
    CrossVerificationRequest,
    CrossVerificationResponse,
)
from app.services.storage_service import storage_service
from app.services.validation_service import validation_service
from app.utils.file_detection import detect_file_type, sanitize_filename
from app.workers.celery_tasks import process_document_task
from app.pipelines.orchestrator import pipeline_orchestrator
from app.utils.logger import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=BatchUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload one or multiple business documents (PDF, JPG, PNG, TIFF, XLSX, XLS, CSV).
    Validates file format, stores locally, and schedules background processing.
    """
    uploaded_docs: List[DocumentResponse] = []
    failed_files: List[dict] = []
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    for file in files:
        filename = sanitize_filename(file.filename or "uploaded_file")
        try:
            content = await file.read()
            if len(content) > max_bytes:
                failed_files.append({"filename": filename, "error": f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB}MB)."})
                continue
            if len(content) == 0:
                failed_files.append({"filename": filename, "error": "File is empty."})
                continue

            # Detect file type using magic bytes + extension
            is_valid, mime_type, normalized_ext = detect_file_type(content, filename)
            if not is_valid:
                failed_files.append({"filename": filename, "error": f"Unsupported or corrupted file type for: {filename}"})
                continue

            # Save file to storage
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = await storage_service.save_file(unique_filename, content)

            # Create document record
            doc = Document(
                user_id=current_user.id if current_user else None,
                filename=filename,
                file_type=normalized_ext.replace(".", "").lower(),
                file_path=file_path,
                status="queued",
                page_count=1,
                needs_review=False
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)

            # Trigger background task or direct eager execution
            if settings.CELERY_TASK_ALWAYS_EAGER or settings.APP_ENV == "test":
                await pipeline_orchestrator.process_document(doc.id, db=db)
            else:
                try:
                    process_document_task.delay(doc.id)
                except Exception as queue_err:
                    logger.warning(f"Celery queue dispatch failed, falling back to direct async execution: {queue_err}")
                    await pipeline_orchestrator.process_document(doc.id, db=db)

            await db.refresh(doc)
            uploaded_docs.append(DocumentResponse.model_validate(doc))

        except Exception as e:
            logger.error(f"Upload processing failed for {filename}: {e}", exc_info=True)
            failed_files.append({"filename": filename, "error": str(e)})

    return BatchUploadResponse(uploaded=uploaded_docs, failed=failed_files)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    needs_review: Optional[bool] = Query(None),
    supplier: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List documents with filtering and pagination."""
    query = select(Document)

    conditions = []
    if status_filter:
        conditions.append(Document.status == status_filter.lower())
    if needs_review is not None:
        conditions.append(Document.needs_review == needs_review)
    if supplier:
        query = query.join(ExtractedData, Document.id == ExtractedData.document_id)
        conditions.append(ExtractedData.supplier_name.ilike(f"%{supplier}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(Document.created_at)).offset(offset).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full details of a document including text, extracted data, validation errors, and history."""
    stmt = select(Document).where(Document.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Fetch relations
    ext_data_stmt = select(ExtractedData).where(ExtractedData.document_id == document_id)
    ext_data = (await db.execute(ext_data_stmt)).scalars().first()

    ext_text_stmt = select(ExtractedText).where(ExtractedText.document_id == document_id).order_by(ExtractedText.page_number)
    ext_texts = (await db.execute(ext_text_stmt)).scalars().all()

    val_err_stmt = select(ValidationError).where(ValidationError.document_id == document_id).order_by(ValidationError.created_at)
    val_errs = (await db.execute(val_err_stmt)).scalars().all()

    corr_stmt = select(CorrectionHistory).where(CorrectionHistory.document_id == document_id).order_by(CorrectionHistory.created_at)
    corrections = (await db.execute(corr_stmt)).scalars().all()

    proc_stmt = select(ProcessingHistory).where(ProcessingHistory.document_id == document_id).order_by(ProcessingHistory.started_at)
    history = (await db.execute(proc_stmt)).scalars().all()

    extracted_schema = None
    if ext_data:
        extracted_schema = ExtractedInvoiceData(
            invoice_number=ext_data.invoice_number,
            invoice_date=ext_data.invoice_date,
            supplier_name=ext_data.supplier_name,
            customer_name=ext_data.customer_name,
            subtotal=ext_data.subtotal,
            tax=ext_data.tax,
            total=ext_data.total,
            currency=ext_data.currency,
            line_items=[LineItem(**item) for item in (ext_data.line_items or []) if isinstance(item, dict)],
            confidence=ext_data.confidence,
            notes=ext_data.notes
        )

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        status=doc.status,
        page_count=doc.page_count,
        needs_review=doc.needs_review,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        extracted_data=extracted_schema,
        extracted_text=[ExtractedTextSchema.model_validate(t) for t in ext_texts],
        validation_errors=[ValidationErrorSchema.model_validate(e) for e in val_errs],
        correction_history=[CorrectionHistorySchema.model_validate(c) for c in corrections],
        processing_history=[ProcessingHistorySchema.model_validate(h) for h in history]
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_db)):
    """Check processing status and estimated progress percentage for polling."""
    stmt = select(Document).where(Document.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    progress = 0
    current_stage = "Queued"

    if doc.status == "queued":
        progress = 10
        current_stage = "Queued in worker queue"
    elif doc.status == "processing":
        # Check latest stage in processing history
        hist_stmt = (
            select(ProcessingHistory)
            .where(ProcessingHistory.document_id == document_id)
            .order_by(desc(ProcessingHistory.started_at))
        )
        latest_hist = (await db.execute(hist_stmt)).scalars().first()
        if latest_hist:
            current_stage = latest_hist.stage.replace("_", " ").title()
            if latest_hist.stage == "text_extraction":
                progress = 35
            elif latest_hist.stage == "ai_extraction":
                progress = 70
            elif latest_hist.stage == "validation":
                progress = 90
        else:
            progress = 25
            current_stage = "Processing started"
    elif doc.status == "completed":
        progress = 100
        current_stage = "Completed"
    elif doc.status == "failed":
        progress = 100
        current_stage = "Failed"

    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        progress=progress,
        current_stage=current_stage,
        needs_review=doc.needs_review,
        error_message=doc.error_message
    )


@router.post("/{document_id}/reprocess", response_model=DocumentStatusResponse)
async def reprocess_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a failed or existing document through the pipeline."""
    stmt = select(Document).where(Document.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    doc.status = "queued"
    doc.error_message = None
    await db.commit()

    try:
        process_document_task.delay(doc.id)
    except Exception as queue_err:
        logger.warning(f"Celery queue error on reprocess, fallback to direct run: {queue_err}")
        await pipeline_orchestrator.process_document(doc.id, db=db)

    return DocumentStatusResponse(
        id=doc.id,
        status="queued",
        progress=10,
        current_stage="Re-queued for processing",
        needs_review=doc.needs_review
    )


@router.patch("/{document_id}/extracted", response_model=DocumentDetailResponse)
async def correct_extracted_data(
    document_id: str,
    payload: ExtractedDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Manually correct extracted invoice fields.
    Updates records, logs modification history, and re-runs validation checks.
    """
    stmt = select(Document).where(Document.id == document_id)
    doc = (await db.execute(stmt)).scalars().first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    ext_stmt = select(ExtractedData).where(ExtractedData.document_id == document_id)
    ext_data = (await db.execute(ext_stmt)).scalars().first()
    if not ext_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extracted data exists for this document yet.")

    # Record changes in correction history
    update_dict = payload.model_dump(exclude_unset=True)
    for field, new_val in update_dict.items():
        old_val = getattr(ext_data, field, None)
        # Check if actually changed
        if str(old_val) != str(new_val):
            corr = CorrectionHistory(
                document_id=doc.id,
                field=field,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
                corrected_by=current_user.id if current_user else "reviewer"
            )
            db.add(corr)
            if field == "line_items" and new_val is not None:
                ext_data.line_items = [item.model_dump() if hasattr(item, "model_dump") else item for item in new_val]
            else:
                setattr(ext_data, field, new_val)

    await db.commit()
    await db.refresh(ext_data)

    # Re-run validation rules on updated data
    data_schema = ExtractedInvoiceData(
        invoice_number=ext_data.invoice_number,
        invoice_date=ext_data.invoice_date,
        supplier_name=ext_data.supplier_name,
        customer_name=ext_data.customer_name,
        subtotal=ext_data.subtotal,
        tax=ext_data.tax,
        total=ext_data.total,
        currency=ext_data.currency,
        line_items=[LineItem(**item) for item in (ext_data.line_items or []) if isinstance(item, dict)],
        confidence=ext_data.confidence,
        notes=ext_data.notes
    )

    # Clear old errors and insert new ones
    from sqlalchemy import delete
    await db.execute(delete(ValidationError).where(ValidationError.document_id == doc.id))

    errors, needs_review = await validation_service.validate_document_data(doc.id, data_schema, db=db)
    for err in errors:
        v_err = ValidationError(
            document_id=doc.id,
            field=err["field"],
            severity=err["severity"],
            message=err["message"]
        )
        db.add(v_err)

    doc.needs_review = needs_review
    await db.commit()

    return await get_document_details(document_id, db)


@router.post("/cross-verify", response_model=CrossVerificationResponse)
async def cross_verify_documents_api(
    payload: CrossVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cross-verify two documents (e.g. PDF invoice against Excel ledger, or PDF against PDF).
    Compares invoice numbers, totals, and supplier names to detect discrepancies.
    """
    doc_a_stmt = select(Document).where(Document.id == payload.primary_document_id)
    doc_a = (await db.execute(doc_a_stmt)).scalars().first()
    if not doc_a:
        raise HTTPException(status_code=404, detail="Primary document not found.")

    doc_b_stmt = select(Document).where(Document.id == payload.reference_document_id)
    doc_b = (await db.execute(doc_b_stmt)).scalars().first()
    if not doc_b:
        raise HTTPException(status_code=404, detail="Reference document not found.")

    data_a_stmt = select(ExtractedData).where(ExtractedData.document_id == doc_a.id)
    data_a = (await db.execute(data_a_stmt)).scalars().first()

    data_b_stmt = select(ExtractedData).where(ExtractedData.document_id == doc_b.id)
    data_b = (await db.execute(data_b_stmt)).scalars().first()

    if not data_a or not data_b:
        raise HTTPException(status_code=400, detail="Both documents must be processed with extracted data before cross-verification.")

    schema_a = ExtractedInvoiceData(
        invoice_number=data_a.invoice_number,
        invoice_date=data_a.invoice_date,
        supplier_name=data_a.supplier_name,
        customer_name=data_a.customer_name,
        subtotal=data_a.subtotal,
        tax=data_a.tax,
        total=data_a.total,
        currency=data_a.currency,
        line_items=[],
        confidence=data_a.confidence
    )

    schema_b = ExtractedInvoiceData(
        invoice_number=data_b.invoice_number,
        invoice_date=data_b.invoice_date,
        supplier_name=data_b.supplier_name,
        customer_name=data_b.customer_name,
        subtotal=data_b.subtotal,
        tax=data_b.tax,
        total=data_b.total,
        currency=data_b.currency,
        line_items=[],
        confidence=data_b.confidence
    )

    return validation_service.cross_verify_documents(
        doc_a_name=doc_a.filename,
        data_a=schema_a,
        doc_b_name=doc_b.filename,
        data_b=schema_b
    )
