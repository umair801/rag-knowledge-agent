from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


# ---------------------------------------------------------------------------
# Translation Request / Response
# ---------------------------------------------------------------------------

class TranslationRequest(BaseModel):
    source_text: str = Field(..., min_length=1, description="Text to translate")
    target_language: str = Field(..., description="Target language name, e.g. 'French'")
    source_language: Optional[str] = Field(
        None, description="Source language name. Auto-detected if not provided."
    )
    style: Optional[str] = Field(
        "literary",
        description="Translation style: literary | formal | casual"
    )


class TranslationResult(BaseModel):
    translated_text: str
    detected_source_language: str
    token_usage: Dict[str, int]
    quality_flag: bool = Field(
        description="True if output length is suspiciously short relative to input"
    )


# ---------------------------------------------------------------------------
# Chapter / Job Schemas
# ---------------------------------------------------------------------------

class Chapter(BaseModel):
    chapter_number: int
    title: Optional[str] = None
    content: str
    word_count: int


class TranslationJob(BaseModel):
    job_id: str
    status: str = Field(description="pending | processing | completed | failed")
    chapter_count: int = 0
    completed_chapters: int = 0
    total_tokens: int = 0
    target_language: str
    style: str = "literary"
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    chapter_count: int
    completed_chapters: int
    total_tokens: int
    progress_percent: float
    error: Optional[str] = None