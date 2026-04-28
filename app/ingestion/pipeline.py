"""
Main ingestion pipeline.
Orchestrates: load → chunk → embed → store (Pinecone + Supabase).
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import structlog

from app.ingestion.loaders import load_document
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_and_store
from app.models.schemas import IngestResponse

load_dotenv()
logger = structlog.get_logger()


def ingest_document(source: str, category: str = "general") -> IngestResponse:
    """
    Full ingestion pipeline for a single document or URL.
    
    Args:
        source: File path or URL
        category: Optional category tag for filtering
    
    Returns:
        IngestResponse with stats
    """
    document_id = str(uuid.uuid4())
    filename = Path(source).name if not source.startswith("http") else source

    logger.info("ingestion_started", source=source, document_id=document_id)

    # Step 1: Load document
    text, source_type, metadata = load_document(source)
    metadata["category"] = category

    if not text.strip():
        raise ValueError(f"No text extracted from: {source}")

    # Step 2: Chunk text
    chunks = chunk_text(
        text=text,
        filename=filename,
        source_type=source_type,
        document_id=document_id,
        source_url=source if source_type == "url" else None,
        metadata=metadata,
    )

    if not chunks:
        raise ValueError(f"No chunks created from: {source}")

    # Step 3: Embed and store in Pinecone
    stored_count = embed_and_store(chunks)

    # Step 4: Log to Supabase
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        supabase.table("rag_documents").insert({
            "id": document_id,
            "filename": filename,
            "source_type": source_type,
            "source_url": source if source_type == "url" else None,
            "chunk_count": stored_count,
            "ingested_at": datetime.now().isoformat(),
            "metadata": metadata,
        }).execute()

        logger.info("supabase_logged", document_id=document_id)

    except Exception as e:
        logger.error("supabase_log_failed", error=str(e))
        # Don't fail the whole pipeline if logging fails

    logger.info(
        "ingestion_complete",
        document_id=document_id,
        chunks=stored_count,
        source_type=source_type,
    )

    return IngestResponse(
        document_id=document_id,
        filename=filename,
        chunks_created=stored_count,
        status="success",
    )


if __name__ == "__main__":
    """Quick test — ingest a sample URL."""
    result = ingest_document(
        source="https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        category="test"
    )
    print(f"\nIngestion Result:")
    print(f"  Document ID : {result.document_id}")
    print(f"  Filename    : {result.filename}")
    print(f"  Chunks      : {result.chunks_created}")
    print(f"  Status      : {result.status}")