# AI-Powered Book Translation Tool

**Built by [Datawebify](https://datawebify.com)**  
**Live:** [translation.datawebify.com](https://translation.datawebify.com)  
**Stack:** Python, FastAPI, OpenAI GPT-4o, PyMuPDF, python-docx, Supabase, Docker, Railway

---

## Overview

A production-grade AI translation system that accepts full-length books in PDF, DOCX,
or TXT format and returns a professionally translated DOCX file, chapter by chapter.
Powered by OpenAI GPT-4o for high-quality literary, formal, and casual translation styles
across 32 supported languages.

---

## Key Features

- Upload PDF, DOCX, or TXT books for end-to-end translation
- Automatic chapter detection: headings, numeric, and roman numeral patterns
- Three translation styles: literary, formal, casual
- Auto language detection via langdetect
- Background job processing with real-time progress polling
- Downloadable translated DOCX preserving chapter structure
- 32 supported languages including Arabic, Urdu, Chinese, Japanese, and more
- Token usage tracking per job
- Quality flagging for suspiciously short translations

---

## Architecture
Client (Browser / API)
│
▼
FastAPI Server
│
┌────┴─────────────────────┐
│                          │
▼                          ▼
/translate/text          /translate/file
(sync, returns result)   (async, returns job_id)
│
┌─────────┴──────────┐
│                    │
▼                    ▼
Document Loader      Chapter Splitter
(PDF/DOCX/TXT)      (boundary detection)
│                    │
└─────────┬──────────┘
▼
GPT-4o Translation Engine
(chapter by chapter)
│
▼
DOCX Builder (python-docx)
│
▼
Job Store + Supabase Logger
│
▼
/jobs/{job_id}/download

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/api/v1/translate/languages` | List all 32 supported languages |
| POST | `/api/v1/translate/text` | Translate a raw text block (sync) |
| POST | `/api/v1/translate/file` | Upload and translate a full book (async) |
| GET | `/api/v1/jobs/{job_id}` | Poll job status and progress |
| GET | `/api/v1/jobs/{job_id}/download` | Download completed translated DOCX |
| GET | `/api/v1/jobs` | List all translation jobs |

---

## Translation Styles

| Style | Description |
|-------|-------------|
| `literary` | Preserves author voice, narrative rhythm, and tone |
| `formal` | Precise, professional, neutral vocabulary |
| `casual` | Conversational, natural, everyday language |

---

## Supported Languages

English, French, Spanish, German, Italian, Portuguese, Dutch, Russian,
Chinese (Simplified), Chinese (Traditional), Japanese, Korean, Arabic,
Turkish, Polish, Swedish, Norwegian, Danish, Finnish, Hindi, Urdu,
Persian, Hebrew, Indonesian, Malay, Thai, Vietnamese, Greek, Czech,
Romanian, Hungarian, Ukrainian

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/umair801/ai-book-translation-tool
cd ai-book-translation-tool
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Run locally

```bash
uvicorn main:app --reload --port 8000
```

### 4. Docker

```bash
docker build -t ai-book-translator .
docker run -p 8000:8000 --env-file .env ai-book-translator
```

---

## Supabase Tables

### `translation_jobs`

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| job_id | text | Unique job identifier |
| status | text | pending / processing / completed / failed |
| target_language | text | Requested translation language |
| style | text | literary / formal / casual |
| chapter_count | int | Total chapters detected |
| completed_chapters | int | Chapters translated so far |
| total_tokens | int | Total GPT-4o tokens used |
| created_at | timestamp | Job creation time |
| updated_at | timestamp | Last status update |

### `translation_documents`

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| job_id | text | Foreign key to translation_jobs |
| filename | text | Original uploaded filename |
| file_type | text | pdf / docx / txt |
| word_count | int | Total words in source document |
| output_path | text | Path to translated DOCX |
| created_at | timestamp | Upload timestamp |

---

## Business Metrics

| Metric | Target |
|--------|--------|
| Average translation speed | Under 2 minutes per 10,000 words |
| Chapter detection accuracy | 95%+ on standard book formats |
| Supported file types | PDF, DOCX, TXT |
| Translation quality flag rate | Under 5% of chapters flagged |
| Token cost per book (80k words) | ~$0.80 at GPT-4o pricing |
| Uptime | 99.9% via Railway deployment |

---

## License

MIT License. Built and maintained by [Datawebify](https://datawebify.com).