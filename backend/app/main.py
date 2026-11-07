"""
FastAPI Main Application Entrypoint.
Configures CORS, rate limiting, request logging middleware, error handlers,
and database lifecycle events.
"""
import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_v1_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and cleanup."""
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        # In PostgreSQL with pgvector, try enabling pgvector extension
        if "postgresql" in settings.DATABASE_URL:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension: {e}")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas initialized.")
    yield
    logger.info("Shutting down application...")
    await engine.dispose()


limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_API])

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Production AI-Powered Document Intelligence and Extraction System.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Attach correlation request ID and log latency."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)
    duration = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    logger.info(
        f"Handled {request.method} {request.url.path} - Status: {response.status_code} in {round(duration * 1000, 2)}ms"
    )
    return response


# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint."""
    provider, api_key, _, model = settings.get_llm_credentials()
    has_key = bool(api_key and not api_key.startswith("your-") and api_key != "mock-or-real-api-key")
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "llm": {
            "provider": provider,
            "model": model,
            "configured": has_key
        }
    }


@app.get("/health/llm", tags=["Health"])
async def llm_health_check():
    """Live roundtrip ping to verify the configured LLM API provider."""
    from app.services.extraction_service import extraction_service
    if not extraction_service.client:
        return {
            "status": "not_configured",
            "provider": extraction_service.provider,
            "message": "No valid API key detected. Heuristic fallback extractor active."
        }
    try:
        start_t = time.time()
        resp = await extraction_service.client.chat.completions.create(
            model=extraction_service.model,
            messages=[{"role": "user", "content": "Respond with: ok"}],
            max_tokens=10
        )
        latency_ms = round((time.time() - start_t) * 1000, 2)
        return {
            "status": "connected",
            "provider": extraction_service.provider,
            "model": extraction_service.model,
            "latency_ms": latency_ms,
            "llm_response": resp.choices[0].message.content.strip()
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": extraction_service.provider,
            "model": extraction_service.model,
            "error": str(e)
        }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Welcome to AI Document Intelligence API.",
        "documentation": f"{settings.API_V1_STR}/docs"
    }
