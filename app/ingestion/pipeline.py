"""
Translation job orchestration pipeline.
Orchestrates: load -> split -> translate -> build DOCX -> log to Supabase.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import structlog

from app.ingestion.loaders import load_document
from app.translation.splitter import split_into_chapters
from app.translation.translator import translate_text
from app.translation.job_store import get_job, update_job
from app.models.schemas import TranslationRequest

load_dotenv()
logger = structlog.get_logger()


def log_job_to_supabase(job_id: str, filename: str, file_type: str, word_count: int, output_path: str) -> None:
    """
    Log a completed translation document to Supabase.
    Non-blocking: logs a warning on failure but does not raise.
    """
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        supabase.table("translation_documents").insert({
            "job_id": job_id,
            "filename": filename,
            "file_type": file_type,
            "word_count": word_count,
            "output_path": output_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.info("supabase_document_logged", job_id=job_id)
    except Exception as e:
        logger.warning("supabase_document_log_failed", error=str(e))


def log_job_status_to_supabase(job_id: str, status: str, target_language: str,
                                style: str, chapter_count: int,
                                completed_chapters: int, total_tokens: int) -> None:
    """
    Upsert job status to translation_jobs Supabase table.
    Non-blocking: logs a warning on failure but does not raise.
    """
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY"),
        )
        supabase.table("translation_jobs").upsert({
            "job_id": job_id,
            "status": status,
            "target_language": target_language,
            "style": style,
            "chapter_count": chapter_count,
            "completed_chapters": completed_chapters,
            "total_tokens": total_tokens,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.info("supabase_job_logged", job_id=job_id, status=status)
    except Exception as e:
        logger.warning("supabase_job_log_failed", error=str(e))