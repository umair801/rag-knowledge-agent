import re
from typing import List
from app.models.schemas import Chapter

# Patterns that signal a chapter boundary
CHAPTER_PATTERNS = [
    r"^\s*(chapter\s+\d+[\.\:]?.*)",           # Chapter 1 / Chapter 1: Title
    r"^\s*(chapter\s+[ivxlcdm]+[\.\:]?.*)",    # Chapter IV / Chapter XII
    r"^\s*(chapter\s+one|two|three|four|five|six|seven|eight|nine|ten"
    r"|eleven|twelve|thirteen|fourteen|fifteen"
    r"|sixteen|seventeen|eighteen|nineteen|twenty"
    r"|thirty|forty|fifty[\w\s]*)",             # Chapter One / Chapter Twenty
    r"^\s*(\d+[\.\)]\s+[A-Z][^\n]{3,})",       # 1. Title / 1) Title
    r"^\s*(CHAPTER\s+\S+.*)",                   # CHAPTER ONE (all caps)
    r"^\s*(PART\s+\d+[\.\:]?.*)",              # PART 1 / PART I
    r"^\s*(PART\s+[IVXLCDM]+[\.\:]?.*)",       # PART IV
]

COMPILED_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.MULTILINE) for p in CHAPTER_PATTERNS
]


def _is_chapter_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    for pattern in COMPILED_PATTERNS:
        if pattern.match(stripped):
            return True
    return False


def _extract_title(line: str) -> str:
    return line.strip()


def _count_words(text: str) -> int:
    return len(text.split())


def split_into_chapters(text: str) -> List[Chapter]:
    lines = text.splitlines()

    # Find all chapter boundary line indices
    boundary_indices = []
    for i, line in enumerate(lines):
        if _is_chapter_heading(line):
            boundary_indices.append(i)

    # If no chapters detected, treat entire text as one chapter
    if not boundary_indices:
        return [
            Chapter(
                chapter_number=1,
                title="Full Text",
                content=text.strip(),
                word_count=_count_words(text),
            )
        ]

    chapters = []
    for idx, start in enumerate(boundary_indices):
        chapter_number = idx + 1
        title = _extract_title(lines[start])

        # Content runs from the line after heading to the next boundary
        content_start = start + 1
        content_end = boundary_indices[idx + 1] if idx + 1 < len(boundary_indices) else len(lines)

        # Join lines, preserving paragraph breaks
        content_lines = lines[content_start:content_end]
        content = "\n".join(content_lines).strip()

        # Never return an empty chapter
        if not content:
            content = title

        chapters.append(
            Chapter(
                chapter_number=chapter_number,
                title=title,
                content=content,
                word_count=_count_words(content),
            )
        )

    return chapters