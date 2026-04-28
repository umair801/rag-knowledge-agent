"""
Metrics tracking module.
Logs every translation job to Supabase for analytics and business reporting.
"""
import os
from datetime import datetime, timezone
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()

# Lazy client -- initialized on first use
_supabase = None

def _get_client():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _supabase = create_client(url, key)
    return _supabase


def log_translation(
    job_id: str,
    target_language: str,
    style: str,
    chapter_count: int,
    total_tokens: int,
    latency_ms: int,
    quality_flag_count: int = 0,
    session_id: Optional[str] = None,
) -> bool:
    """
    Log a completed translation job to Supabase translation_jobs table.

    Returns True on success, False on failure.
    """
    try:
        _get_client().table("translation_jobs").upsert({
            "job_id": job_id,
            "target_language": target_language,
            "style": style,
            "chapter_count": chapter_count,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "quality_flag_count": quality_flag_count,
            "session_id": session_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info(
            "translation_logged",
            job_id=job_id,
            latency_ms=latency_ms,
            total_tokens=total_tokens,
        )
        return True

    except Exception as e:
        logger.error("translation_log_failed", error=str(e))
        return False


def get_metrics_summary() -> dict:
    """
    Pull aggregate translation metrics from Supabase.
    Returns business-ready summary stats.
    """
    try:
        result = _get_client().table("translation_jobs").select(
            "latency_ms, total_tokens, chapter_count, quality_flag_count, created_at, session_id"
        ).execute()

        rows = result.data

        if not rows:
            return {
                "total_jobs": 0,
                "avg_latency_ms": 0,
                "avg_tokens_per_job": 0,
                "avg_chapters_per_job": 0,
                "jobs_under_2min": 0,
                "jobs_under_2min_pct": 0,
                "quality_flag_rate_pct": 0,
                "unique_sessions": 0,
                "report_generated_at": datetime.now(timezone.utc).isoformat(),
            }

        total = len(rows)
        avg_latency = round(sum(r["latency_ms"] for r in rows if r["latency_ms"]) / total)
        avg_tokens = round(sum(r["total_tokens"] for r in rows if r["total_tokens"]) / total)
        avg_chapters = round(sum(r["chapter_count"] for r in rows if r["chapter_count"]) / total, 1)
        under_2min = sum(1 for r in rows if r["latency_ms"] and r["latency_ms"] < 120000)
        total_chapters = sum(r["chapter_count"] for r in rows if r["chapter_count"])
        flagged = sum(r["quality_flag_count"] for r in rows if r["quality_flag_count"])
        flag_rate = round((flagged / total_chapters) * 100, 1) if total_chapters > 0 else 0
        unique_sessions = len(set(r["session_id"] for r in rows if r["session_id"]))

        return {
            "total_jobs": total,
            "avg_latency_ms": avg_latency,
            "avg_tokens_per_job": avg_tokens,
            "avg_chapters_per_job": avg_chapters,
            "jobs_under_2min": under_2min,
            "jobs_under_2min_pct": round((under_2min / total) * 100, 1),
            "quality_flag_rate_pct": flag_rate,
            "unique_sessions": unique_sessions,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("metrics_fetch_failed", error=str(e))
        return {}