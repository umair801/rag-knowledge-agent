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
        title="AI-Powered Book Translation Tool",
        description=(
            "Production-grade book translation system. "
            "Upload PDF, DOCX, or TXT files and receive fully translated DOCX output, "
            "chapter by chapter, powered by GPT-4o across 32 languages."
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

    # Serve translation UI at root
    @app.get("/", include_in_schema=False)
    async def root():
        index_path = os.path.join(static_dir, "index.html")
        return FileResponse(index_path)

    # Health check at root level (no prefix)
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "AI-Powered Book Translation Tool"}

    # Mount API routes (routes already carry /api/v1 prefix internally)
    app.include_router(router)

    @app.on_event("startup")
    async def startup():
        logger.info("translation_api_started", version="1.0.0")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("translation_api_stopped")

    return app


app = create_app()