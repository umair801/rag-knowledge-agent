"""
FastAPI application factory.
Serves chat UI at root and mounts all API routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import structlog
import os

from app.api.routes import router

logger = structlog.get_logger()


def create_app() -> FastAPI:
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve static files
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    static_dir = os.path.abspath(static_dir)

    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Serve chat UI at root
    @app.get("/", include_in_schema=False)
    async def root():
        index_path = os.path.join(static_dir, "index.html")
        return FileResponse(index_path)

    # Mount API routes
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup():
        logger.info("rag_api_started", version="1.0.0")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("rag_api_stopped")

    return app


app = create_app()