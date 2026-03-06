"""
Semantic retrieval module.
Converts a query to a vector and finds the most relevant chunks in Pinecone.
"""
import os
from typing import List
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()

EMBEDDING_MODEL = "text-embedding-3-small"

# Initialize clients once at module load — not on every query
_openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
_index = _pc.Index(os.getenv("PINECONE_INDEX_NAME", "rag-knowledge-base"))


def retrieve_chunks(
    query: str,
    top_k: int = 5,
    filter_source: str | None = None,
    filter_category: str | None = None,
    filter_filename: str | None = None,
) -> List[dict]:
    """
    Embed the query and retrieve top-k matching chunks from Pinecone.

    Args:
        query: User's question
        top_k: Number of chunks to retrieve
        filter_source: Filter by source_type ('pdf', 'docx', 'url', 'txt')
        filter_category: Filter by category tag set during ingestion
        filter_filename: Filter by specific document filename

    Returns:
        List of matched chunks with content and metadata
    """
    # Embed the query
    try:
        response = _openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query.replace("\n", " "),
        )
        query_vector = response.data[0].embedding
    except Exception as e:
        logger.error("query_embedding_failed", error=str(e))
        raise

    # Build compound metadata filter
    filters = []
    if filter_source:
        filters.append({"source_type": {"$eq": filter_source}})
    if filter_category:
        filters.append({"category": {"$eq": filter_category}})
    if filter_filename:
        filters.append({"filename": {"$eq": filter_filename}})

    pinecone_filter = None
    if len(filters) == 1:
        pinecone_filter = filters[0]
    elif len(filters) > 1:
        pinecone_filter = {"$and": filters}

    # Query Pinecone
    try:
        results = _index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=pinecone_filter,
        )
    except Exception as e:
        logger.error("pinecone_query_failed", error=str(e))
        raise

    # Parse results
    chunks = []
    for match in results.matches:
        chunks.append({
            "chunk_id": match.id,
            "score": round(match.score, 4),
            "content": match.metadata.get("content", ""),
            "filename": match.metadata.get("filename", ""),
            "source_type": match.metadata.get("source_type", ""),
            "source_url": match.metadata.get("source_url", ""),
            "document_id": match.metadata.get("document_id", ""),
            "chunk_index": match.metadata.get("chunk_index", 0),
            "category": match.metadata.get("category", ""),
        })

    logger.info(
        "chunks_retrieved",
        query=query[:60],
        top_k=top_k,
        results=len(chunks),
        top_score=chunks[0]["score"] if chunks else 0,
        filters_applied=len(filters),
    )

    return chunks