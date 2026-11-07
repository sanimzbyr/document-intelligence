"""
Celery worker tasks for asynchronous document processing.
"""
import asyncio
from celery import shared_task
from app.core.celery_app import celery_app
from app.pipelines.orchestrator import pipeline_orchestrator
from app.utils.logger import logger


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_document_task(self, document_id: str):
    """
    Celery task to run document processing pipeline asynchronously.
    Retries up to 3 times on transient failures with exponential backoff.
    """
    logger.info(f"Celery task received for document_id: {document_id}")
    try:
        # Use asyncio.run for worker subprocess
        success = asyncio.run(pipeline_orchestrator.process_document(document_id))
        if not success:
            logger.warning(f"Pipeline returned failure for document {document_id}")
        return {"document_id": document_id, "success": success}
    except Exception as exc:
        logger.error(f"Task exception for document {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
