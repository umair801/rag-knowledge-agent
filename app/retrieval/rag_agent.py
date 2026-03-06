"""
RAG Query Agent with conversation memory.
Orchestrates: embed query → retrieve chunks → generate answer → store history.
"""
import os
import time
from dotenv import load_dotenv
import structlog

from app.retrieval.retriever import retrieve_chunks
from app.retrieval.generator import generate_answer
from app.retrieval.memory import create_session, get_history, add_turn
from app.models.schemas import QueryRequest, QueryResponse
from app.metrics.tracker import log_query

load_dotenv()
logger = structlog.get_logger()


def run_query(request: QueryRequest) -> QueryResponse:
    """
    Execute a full RAG query pipeline with conversation memory.

    Args:
        request: QueryRequest with query, options, and optional session_id

    Returns:
        QueryResponse with answer, sources, score, latency, and session_id
    """
    start_time = time.time()

    # Create new session if none provided
    session_id = request.session_id or create_session()

    logger.info("query_started", query=request.query[:80], session_id=session_id)

    # Step 1: Retrieve relevant chunks
    chunks = retrieve_chunks(
        query=request.query,
        top_k=request.top_k,
        filter_source=request.filter_source,
        filter_category=getattr(request, "filter_category", None),
        filter_filename=getattr(request, "filter_filename", None),
    )
    # Step 2: Get conversation history for this session
    chat_history = get_history(session_id)

    # Step 3: Generate answer with context + history
    answer = generate_answer(
        query=request.query,
        chunks=chunks,
        chat_history=chat_history if chat_history else None,
    )

    # Step 4: Save this turn to memory
    add_turn(session_id=session_id, query=request.query, answer=answer)

    # Step 5: Calculate metrics
    latency_ms = int((time.time() - start_time) * 1000)
    top_score = chunks[0]["score"] if chunks else 0.0

    # Step 6: Deduplicate sources
    seen = {}
    for c in chunks:
        key = c["source_url"] or c["filename"]
        if key not in seen or c["score"] > seen[key]["score"]:
            seen[key] = {
                "filename": c["filename"],
                "source_url": c["source_url"],
                "score": c["score"],
            }
    sources = list(seen.values())

    # Step 7: Log metrics to Supabase (non-blocking -- never fails the query)
    log_query(
        query_text=request.query,
        response_text=answer,
        sources_used=sources,
        retrieval_score=top_score,
        latency_ms=latency_ms,
        session_id=session_id,
    )
    
    logger.info(
        "query_complete",
        session_id=session_id,
        latency_ms=latency_ms,
        top_score=top_score,
        sources=len(sources),
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        retrieval_score=top_score,
        latency_ms=latency_ms,
        session_id=session_id,
    )


if __name__ == "__main__":
    """Test metadata filtering -- restrict retrieval by source type."""
    from app.retrieval.memory import create_session

    session_id = create_session()

    tests = [
        # No filter -- searches everything
        QueryRequest(
            query="What is retrieval augmented generation?",
            top_k=4,
            session_id=session_id,
        ),
        # Filter by source type -- only URL sources
        QueryRequest(
            query="What is retrieval augmented generation?",
            top_k=4,
            filter_source="url",
            session_id=session_id,
        ),
        # Filter by category
        QueryRequest(
            query="What is retrieval augmented generation?",
            top_k=4,
            filter_category="test",
            session_id=session_id,
        ),
    ]

    labels = ["No filter", "Filter: source=url", "Filter: category=test"]

    for label, request in zip(labels, tests):
        print(f"\n{'='*60}")
        print(f"Test: {label}")
        print(f"Q: {request.query}")
        print(f"{'='*60}")
        response = run_query(request)
        print(f"A: {response.answer[:200]}...")
        print(f"Sources : {len(response.sources)}")
        print(f"Latency : {response.latency_ms}ms")