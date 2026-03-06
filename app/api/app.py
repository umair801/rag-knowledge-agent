"""
FastAPI application factory.
Configures middleware, CORS, and mounts all routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.api.routes import router

logger = structlog.get_logger()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="RAG Knowledge Base Agent",
        description=(
            "Enterprise RAG system -- instant answers from your documents. "
            "Supports PDF, DOCX, TXT, and URL ingestion with semantic search "
            "and GPT-4o-mini response generation."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS -- allow all origins for SaaS integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount all routes
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup():
        logger.info("rag_api_started", version="1.0.0")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("rag_api_stopped")

    return app


app = create_app()