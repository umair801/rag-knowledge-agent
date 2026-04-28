from typing import Dict
from app.models.schemas import TranslationJob

# In-memory job store: job_id -> TranslationJob
_jobs: Dict[str, TranslationJob] = {}


def create_job(job: TranslationJob) -> None:
    _jobs[job.job_id] = job


def get_job(job_id: str) -> TranslationJob | None:
    return _jobs.get(job_id)


def update_job(job: TranslationJob) -> None:
    _jobs[job.job_id] = job


def all_jobs() -> Dict[str, TranslationJob]:
    return _jobs