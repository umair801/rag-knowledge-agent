"""
Document loaders for PDF, DOCX, TXT, and URL sources.
Each loader returns raw text for the chunker to process.
"""
import os
import requests
import structlog
from pathlib import Path
from typing import Tuple

logger = structlog.get_logger()


def load_pdf(filepath: str) -> Tuple[str, dict]:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(filepath)
        text_parts = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(text)

        full_text = "\n\n".join(text_parts)
        metadata = {
            "page_count": len(doc),
            "file_size_bytes": os.path.getsize(filepath),
        }

        logger.info("pdf_loaded", filepath=filepath, pages=len(doc))
        return full_text, metadata

    except Exception as e:
        logger.error("pdf_load_failed", filepath=filepath, error=str(e))
        raise


def load_docx(filepath: str) -> Tuple[str, dict]:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document

        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)

        metadata = {
            "paragraph_count": len(paragraphs),
            "file_size_bytes": os.path.getsize(filepath),
        }

        logger.info("docx_loaded", filepath=filepath, paragraphs=len(paragraphs))
        return full_text, metadata

    except Exception as e:
        logger.error("docx_load_failed", filepath=filepath, error=str(e))
        raise


def load_txt(filepath: str) -> Tuple[str, dict]:
    """Load plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        metadata = {"file_size_bytes": os.path.getsize(filepath)}
        logger.info("txt_loaded", filepath=filepath)
        return text, metadata

    except Exception as e:
        logger.error("txt_load_failed", filepath=filepath, error=str(e))
        raise


def load_url(url: str) -> Tuple[str, dict]:
    """Scrape and extract clean text from a URL."""
    try:
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (RAG Knowledge Agent)"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_text = "\n".join(lines)

        metadata = {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(full_text),
        }

        logger.info("url_loaded", url=url, chars=len(full_text))
        return full_text, metadata

    except Exception as e:
        logger.error("url_load_failed", url=url, error=str(e))
        raise


def load_document(source: str) -> Tuple[str, str, dict]:
    """
    Auto-detect source type and load document.
    Returns: (text, source_type, metadata)
    """
    if source.startswith("http://") or source.startswith("https://"):
        text, meta = load_url(source)
        return text, "url", meta

    path = Path(source)
    ext = path.suffix.lower()

    if ext == ".pdf":
        text, meta = load_pdf(source)
        return text, "pdf", meta
    elif ext == ".docx":
        text, meta = load_docx(source)
        return text, "docx", meta
    elif ext == ".txt":
        text, meta = load_txt(source)
        return text, "txt", meta
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: pdf, docx, txt, url")