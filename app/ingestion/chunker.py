"""
Text chunking module.
Splits large documents into smaller overlapping chunks for embedding.
"""
import uuid
from typing import List
import tiktoken
import structlog

from app.models.schemas import DocumentChunk

logger = structlog.get_logger()

# Target chunk size in tokens (not characters)
CHUNK_SIZE_TOKENS = 400
CHUNK_OVERLAP_TOKENS = 80


def count_tokens(text: str, model: str = "text-embedding-3-small") -> int:
    """Count tokens in a string using tiktoken."""
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_text(
    text: str,
    filename: str,
    source_type: str,
    document_id: str,
    source_url: str | None = None,
    metadata: dict | None = None,
) -> List[DocumentChunk]:
    """
    Split text into overlapping chunks of ~400 tokens each.
    Overlap ensures context is not lost at chunk boundaries.
    """
    if not text.strip():
        logger.warning("empty_text_received", filename=filename)
        return []

    if metadata is None:
        metadata = {}

    # Split into sentences first (crude but effective)
    sentences = text.replace("\n\n", "\n").split(". ")
    
    chunks: List[DocumentChunk] = []
    current_chunk: List[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_tokens = count_tokens(sentence)

        # If adding this sentence exceeds chunk size, save current chunk
        if current_tokens + sentence_tokens > CHUNK_SIZE_TOKENS and current_chunk:
            chunk_text_str = ". ".join(current_chunk) + "."
            chunks.append(
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    filename=filename,
                    source_type=source_type,
                    source_url=source_url,
                    content=chunk_text_str,
                    chunk_index=len(chunks),
                    total_chunks=0,  # updated after all chunks created
                    metadata=metadata,
                )
            )

            # Overlap: keep last few sentences for context continuity
            overlap_sentences: List[str] = []
            overlap_tokens = 0
            for s in reversed(current_chunk):
                s_tokens = count_tokens(s)
                if overlap_tokens + s_tokens <= CHUNK_OVERLAP_TOKENS:
                    overlap_sentences.insert(0, s)
                    overlap_tokens += s_tokens
                else:
                    break

            current_chunk = overlap_sentences
            current_tokens = overlap_tokens

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Don't forget the last chunk
    if current_chunk:
        chunk_text_str = ". ".join(current_chunk) + "."
        chunks.append(
            DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                filename=filename,
                source_type=source_type,
                source_url=source_url,
                content=chunk_text_str,
                chunk_index=len(chunks),
                total_chunks=0,
                metadata=metadata,
            )
        )

    # Update total_chunks on all items
    total = len(chunks)
    for chunk in chunks:
        chunk.total_chunks = total

    logger.info("text_chunked", filename=filename, chunks=total)
    return chunks