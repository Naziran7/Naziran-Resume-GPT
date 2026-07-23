import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.core.limiter import limiter
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)

# Setup logging configuration on startup
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup table creation and resource cleanup."""
    try:
        from app.core.db import engine, Base
        import app.models  # Register all models for metadata binding
        async with engine.begin() as conn:
            try:
                from sqlalchemy import text
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension: {e}")
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schema on startup: {e}")
    yield

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NaziranGPT - AI-Powered Career Intelligence Platform Backend Services",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Connect slowapi rate limiter to app state and register its exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup custom global exception handlers
setup_exception_handlers(app)

# Apply CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include main versioned routing
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": f"{settings.API_V1_STR}/docs"
    }
