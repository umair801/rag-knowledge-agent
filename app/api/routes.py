"""
FastAPI route definitions.
Exposes /ingest, /chat, /history, /metrics, and /health endpoints.
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import shutil
import tempfile
import structlog

from app.ingestion.pipeline import ingest_document
from app.retrieval.rag_agent import run_query
from app.retrieval.memory import (
    create_session,
    get_history,
    delete_session,
    get_session_stats,
)
from app.metrics.tracker import get_metrics_summary
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    IngestRequest,
    IngestResponse,
)

logger = structlog.get_logger()
router = APIRouter()


# ─── Health Check ────────────────────────────────────────────
@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Knowledge Base Agent",
        "version": "1.0.0",
    }


# ─── Ingest: File Upload ──────────────────────────────────────
@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
):
    """
    Upload and ingest a document file (PDF, DOCX, TXT).
    Chunks, embeds, and stores in Pinecone automatically.
    """
    allowed_types = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT",
        )

    # Save to temp file for processing
    suffix = allowed_types[file.content_type]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_document(source=tmp_path, category=category)
        # Use original filename in response
        result.filename = file.filename
        logger.info("file_ingested", filename=file.filename, chunks=result.chunks_created)
        return result
    except Exception as e:
        logger.error("file_ingest_failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


# ─── Ingest: URL ──────────────────────────────────────────────
@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: IngestRequest):
    """
    Ingest content from a public URL.
    Scrapes, chunks, embeds, and stores automatically.
    """
    try:
        result = ingest_document(
            source=request.url,
            category=request.category or "general",
        )
        logger.info("url_ingested", url=request.url, chunks=result.chunks_created)
        return result
    except Exception as e:
        logger.error("url_ingest_failed", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── Chat ─────────────────────────────────────────────────────
@router.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """
    Submit a question to the RAG knowledge base.
    Returns a grounded answer with sources and metrics.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        response = run_query(request)
        return response
    except Exception as e:
        logger.error("chat_failed", query=request.query[:60], error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ─── Session: New ─────────────────────────────────────────────
@router.post("/session/new")
async def new_session():
    """Create a new conversation session."""
    session_id = create_session()
    return {"session_id": session_id}


# ─── Session: History ─────────────────────────────────────────
@router.get("/session/{session_id}/history")
async def session_history(session_id: str):
    """Retrieve conversation history for a session."""
    history = get_history(session_id)
    stats = get_session_stats(session_id)

    if stats is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    return {
        "session_id": session_id,
        "turn_count": stats["turn_count"],
        "messages": history,
    }


# ─── Session: Delete ──────────────────────────────────────────
@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """Delete a session and clear its history."""
    deleted = delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}


# ─── Metrics ──────────────────────────────────────────────────
@router.get("/metrics")
async def metrics():
    """Return system performance metrics."""
    stats = get_metrics_summary()
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to fetch metrics")
    return stats


# ─── Documents List ───────────────────────────────────────────
@router.get("/documents")
async def list_documents():
    """List all ingested documents from Supabase."""
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        result = supabase.table("documents").select(
            "id, filename, source_type, chunk_count, ingested_at, metadata"
        ).order("ingested_at", desc=True).execute()

        return {
            "total_documents": len(result.data),
            "documents": result.data,
        }
    except Exception as e:
        logger.error("documents_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))