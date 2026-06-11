from pathlib import Path

from core.analysis_models import JobAnalysis
from core.database import initialize_database
from core.models import Job
from repositories.analyses_repository import AnalysesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository


def test_analyses_repository_counts_by_classification_and_score_range(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    source_id = _create_source(database_path)
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(source_id, "Job 1", "hash-1"),
            _job(source_id, "Job 2", "hash-2"),
            _job(source_id, "Job 3", "hash-3"),
        ]
    )
    jobs = jobs_repository.list_all()
    analyses_repository = AnalysesRepository(database_path)
    analyses_repository.upsert(
        JobAnalysis(id=None, job_id=jobs[0].id, score=30, classification="Ignorar")
    )
    analyses_repository.upsert(
        JobAnalysis(id=None, job_id=jobs[1].id, score=60, classification="Avaliar")
    )
    analyses_repository.upsert(
        JobAnalysis(id=None, job_id=jobs[2].id, score=90, classification="Aplicar")
    )

    assert analyses_repository.count_by_classification() == {
        "Aplicar": 1,
        "Avaliar": 1,
        "Ignorar": 1,
    }
    assert analyses_repository.count_by_score_range() == {
        "0-49": 1,
        "50-69": 1,
        "70-100": 1,
    }


def _create_source(database_path: Path) -> int:
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    return sources_repository.list_all()[0].id


def _job(source_id: int, title: str, content_hash: str) -> Job:
    return Job(
        id=None,
        source_id=source_id,
        email_message_id=None,
        title=title,
        content_hash=content_hash,
    )
