"""
Metrics tracking module.
Logs every query to Supabase for analytics and business reporting.
"""
import os
from datetime import datetime, timezone
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()

# Initialize Supabase client once
_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


def log_query(
    query_text: str,
    response_text: str,
    sources_used: list,
    retrieval_score: float,
    latency_ms: int,
    session_id: Optional[str] = None,
) -> bool:
    """
    Log a completed query to Supabase query_logs table.

    Returns True on success, False on failure.
    """
    try:
        _supabase.table("query_logs").insert({
            "query_text": query_text,
            "response_text": response_text,
            "sources_used": sources_used,
            "retrieval_score": retrieval_score,
            "latency_ms": latency_ms,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info(
            "query_logged",
            latency_ms=latency_ms,
            retrieval_score=retrieval_score,
            session_id=session_id,
        )
        return True

    except Exception as e:
        logger.error("query_log_failed", error=str(e))
        return False


def get_metrics_summary() -> dict:
    """
    Pull aggregate metrics from Supabase.
    Returns business-ready summary stats.
    """
    try:
        # Fetch all query logs
        result = _supabase.table("query_logs").select(
            "latency_ms, retrieval_score, created_at, session_id"
        ).execute()

        rows = result.data

        if not rows:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0,
                "avg_retrieval_score": 0,
                "queries_under_3s": 0,
                "queries_under_3s_pct": 0,
                "unique_sessions": 0,
                "report_generated_at": datetime.now(timezone.utc).isoformat(),
            }

        total = len(rows)
        avg_latency = round(sum(r["latency_ms"] for r in rows) / total)
        avg_score = round(
            sum(r["retrieval_score"] for r in rows if r["retrieval_score"]) / total, 4
        )
        under_3s = sum(1 for r in rows if r["latency_ms"] < 3000)
        unique_sessions = len(set(r["session_id"] for r in rows if r["session_id"]))

        return {
            "total_queries": total,
            "avg_latency_ms": avg_latency,
            "avg_retrieval_score": avg_score,
            "queries_under_3s": under_3s,
            "queries_under_3s_pct": round((under_3s / total) * 100, 1),
            "unique_sessions": unique_sessions,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("metrics_fetch_failed", error=str(e))
        return {}