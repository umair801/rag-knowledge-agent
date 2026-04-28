"""
Embedding and vector storage module.
Converts text chunks to vectors and stores them in Pinecone.
"""
import os
import time
from typing import List
from openai import OpenAI
from pinecone import Pinecone
import structlog

from app.models.schemas import DocumentChunk

logger = structlog.get_logger()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100  # Pinecone upsert batch size


def get_embedding(text: str, client: OpenAI) -> List[float]:
    """Generate a single embedding vector for a text string."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.replace("\n", " "),
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        raise


def embed_and_store(chunks: List[DocumentChunk]) -> int:
    """
    Generate embeddings for all chunks and upsert into Pinecone.
    Returns number of vectors stored.
    """
    if not chunks:
        logger.warning("no_chunks_to_embed")
        return 0

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "rag-knowledge-base"))

    vectors = []

    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk.content, openai_client)

            vectors.append({
                "id": chunk.chunk_id,
                "values": embedding,
                "metadata": {
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "source_type": chunk.source_type,
                    "source_url": chunk.source_url or "",
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "content": chunk.content[:1000],  # Store preview in metadata
                    **chunk.metadata,
                },
            })

            # Small delay to respect OpenAI rate limits
            if (i + 1) % 10 == 0:
                time.sleep(0.5)
                logger.info("embedding_progress", done=i + 1, total=len(chunks))

        except Exception as e:
            logger.error("chunk_embedding_failed", chunk_id=chunk.chunk_id, error=str(e))
            continue

    # Upsert in batches
    stored = 0
    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i : i + BATCH_SIZE]
        try:
            index.upsert(vectors=batch)
            stored += len(batch)
            logger.info("pinecone_upsert", batch_size=len(batch), total_stored=stored)
        except Exception as e:
            logger.error("pinecone_upsert_failed", error=str(e))

    return stored