"""
Document Processing Orchestrator.
Coordinates the end-to-end pipeline:
1. Ingestion status update
2. Multi-page / multi-format text extraction
3. AI structured information extraction
4. Financial rule validation and duplicate detection
5. History tracking and completion status
"""
import traceback
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.models.models import (
    Document,
    ExtractedText,
    ExtractedData,
    ValidationError,
    ProcessingHistory,
)
from app.pipelines.text_extractor import text_extractor
from app.services.extraction_service import extraction_service
from app.services.validation_service import validation_service
from app.services.search_service import search_service
from app.utils.logger import logger


class PipelineOrchestrator:
    async def process_document(self, document_id: str, db: Optional[AsyncSession] = None) -> bool:
        """
        Execute full pipeline for a given document.
        Can run with an existing session or open a dedicated session.
        """
        if db:
            return await self._run_pipeline(document_id, db)
        else:
            async with AsyncSessionLocal() as session:
                try:
                    success = await self._run_pipeline(document_id, session)
                    await session.commit()
                    return success
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Pipeline error for document {document_id}: {e}", exc_info=True)
                    return False

    async def _run_pipeline(self, document_id: str, session: AsyncSession) -> bool:
        stmt = select(Document).where(Document.id == document_id)
        document = (await session.execute(stmt)).scalars().first()
        if not document:
            logger.error(f"Document with id {document_id} not found.")
            return False

        # Set status to processing
        document.status = "processing"
        document.error_message = None
        await session.commit()

        # Helper to log history stages
        async def record_stage(stage: str, status: str, error: Optional[str] = None):
            h = ProcessingHistory(
                document_id=document.id,
                stage=stage,
                status=status,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc) if status != "started" else None,
                error=error
            )
            session.add(h)
            await session.commit()

        try:
            # -------------------------------------------------------------
            # Stage 1: Text Extraction
            # -------------------------------------------------------------
            await record_stage("text_extraction", "started")
            logger.info(f"Extracting text from: {document.file_path}")
            
            pages_data = text_extractor.extract(document.file_path, document.file_type)
            document.page_count = len(pages_data)

            # Clear any prior extracted text (for reprocessing)
            await session.execute(delete(ExtractedText).where(ExtractedText.document_id == document.id))

            all_page_texts = []
            for item in pages_data:
                page_text = item["text"]
                all_page_texts.append(page_text)
                
                # Generate vector embedding for semantic search
                embedding = await search_service.get_embedding(page_text) if page_text else None

                ext_text = ExtractedText(
                    document_id=document.id,
                    page_number=item["page_number"],
                    text=page_text,
                    embedding=embedding
                )
                session.add(ext_text)

            await session.commit()
            await record_stage("text_extraction", "completed")

            # -------------------------------------------------------------
            # Stage 2: AI Information Extraction
            # -------------------------------------------------------------
            await record_stage("ai_extraction", "started")
            combined_text = "\n\n".join(all_page_texts)
            logger.info(f"Invoking AI extraction for doc {document.id} ({len(combined_text)} characters)")

            extracted_invoice = await extraction_service.extract_information(combined_text)

            # Clear prior extracted data
            await session.execute(delete(ExtractedData).where(ExtractedData.document_id == document.id))

            # Save structured extracted data
            db_extracted = ExtractedData(
                document_id=document.id,
                invoice_number=extracted_invoice.invoice_number,
                invoice_date=extracted_invoice.invoice_date,
                supplier_name=extracted_invoice.supplier_name,
                customer_name=extracted_invoice.customer_name,
                subtotal=extracted_invoice.subtotal,
                tax=extracted_invoice.tax,
                total=extracted_invoice.total,
                currency=extracted_invoice.currency,
                line_items=[item.model_dump() for item in extracted_invoice.line_items],
                confidence=extracted_invoice.confidence,
                notes=extracted_invoice.notes
            )
            session.add(db_extracted)
            await session.commit()
            await record_stage("ai_extraction", "completed")

            # -------------------------------------------------------------
            # Stage 3: Data Validation & Reconciliation
            # -------------------------------------------------------------
            await record_stage("validation", "started")
            logger.info(f"Validating financial rules for doc {document.id}")

            # Clear prior validation errors
            await session.execute(delete(ValidationError).where(ValidationError.document_id == document.id))

            validation_errors, needs_review = await validation_service.validate_document_data(
                document_id=document.id,
                data=extracted_invoice,
                db=session
            )

            for err in validation_errors:
                v_err = ValidationError(
                    document_id=document.id,
                    field=err["field"],
                    severity=err["severity"],
                    message=err["message"]
                )
                session.add(v_err)

            document.needs_review = needs_review
            document.status = "completed"
            await session.commit()
            await record_stage("validation", "completed")

            logger.info(f"Document processing completed successfully: {document.id}")
            return True

        except Exception as e:
            error_details = str(e)
            stack = traceback.format_exc()
            logger.error(f"Pipeline failure for document {document_id}: {error_details}\n{stack}")
            document.status = "failed"
            document.error_message = error_details
            await record_stage("pipeline", "failed", error=error_details)
            await session.commit()
            return False


pipeline_orchestrator = PipelineOrchestrator()
