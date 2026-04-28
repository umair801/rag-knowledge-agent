"""
Core data models for the RAG Knowledge Base Agent.
All data structures are defined here for consistency across modules.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A single chunk of text extracted from a document."""
    chunk_id: str
    document_id: str
    filename: str
    source_type: str  # 'pdf', 'docx', 'url', 'txt'
    source_url: Optional[str] = None
    content: str
    chunk_index: int
    total_chunks: int
    metadata: dict = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Request model for URL ingestion via API."""
    url: str
    category: Optional[str] = "general"


class IngestResponse(BaseModel):
    """Response model after document ingestion."""
    document_id: str
    filename: str
    chunks_created: int
    status: str
    ingested_at: datetime = Field(default_factory=datetime.now)


class QueryRequest(BaseModel):
    """Request model for a RAG query."""
    query: str
    top_k: int = 5
    filter_source: Optional[str] = None      # filter by source_type: 'pdf','url','docx','txt'
    filter_category: Optional[str] = None    # filter by category tag set at ingestion
    filter_filename: Optional[str] = None    # filter by specific filename
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for a RAG query."""
    answer: str
    sources: list[dict]
    retrieval_score: float
    latency_ms: int
    session_id: Optional[str] = None