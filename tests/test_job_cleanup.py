from datetime import date
from pathlib import Path

from core.database import initialize_database
from core.models import EmailMessage, Job
from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.user_repository import UserRepository
from services.job_cleanup_service import JobCleanupService


def test_cleanup_marks_duplicate_jobs_and_keeps_first_as_new(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    source_id = _prepare_database(database_path)
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(
                source_id=source_id,
                title="Frontend Developer",
                company="Acme",
                job_url="https://example.com/jobs/123?utm_source=email",
                content_hash="hash-1",
            ),
            _job(
                source_id=source_id,
                title="Frontend Developer",
                company="Acme",
                job_url="https://example.com/jobs/123?ref=alert",
                content_hash="hash-2",
            ),
        ]
    )

    summary = JobCleanupService(database_path).cleanup_jobs(today=date(2026, 6, 10))
    jobs = jobs_repository.list_all()

    assert summary.reviewed_jobs == 2
    assert summary.duplicate_jobs == 1
    assert jobs[0].status == "new"
    assert jobs[1].status == "duplicate"


def test_cleanup_marks_digest_container_job_as_duplicate(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    source_id = _prepare_database(database_path)
    EmailMessagesRepository(database_path).insert_many_ignore_existing(
        [
            EmailMessage(
                id=None,
                source_id=source_id,
                gmail_message_id="msg-1",
                gmail_thread_id="thread-1",
                gmail_label_name="Job Alerts",
            )
        ]
    )
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(
                source_id=source_id,
                title="Novas vagas em Brasil. Candidate-se agora.",
                content_hash="hash-1",
                email_message_id=1,
            ),
            _job(
                source_id=source_id,
                title="Desenvolvedor React",
                company="Acme",
                content_hash="hash-2",
                email_message_id=1,
            ),
        ]
    )

    summary = JobCleanupService(database_path).cleanup_jobs(today=date(2026, 6, 10))
    jobs = jobs_repository.list_all()

    assert summary.duplicate_jobs == 1
    assert jobs[0].status == "duplicate"
    assert jobs[1].status == "new"


def test_cleanup_marks_old_jobs(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    source_id = _prepare_database(database_path)
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(
                source_id=source_id,
                title="Backend Developer",
                posted_at="2026-03-01",
                content_hash="hash-1",
            ),
            _job(
                source_id=source_id,
                title="Frontend Developer",
                posted_at="2026-06-01",
                content_hash="hash-2",
            ),
        ]
    )

    summary = JobCleanupService(database_path).cleanup_jobs(
        max_age_days=45,
        today=date(2026, 6, 10),
    )
    jobs = jobs_repository.list_all()

    assert summary.old_jobs == 1
    assert jobs[0].status == "old"
    assert jobs[1].status == "new"


def test_cleanup_marks_incompatible_jobs_from_preferences(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    source_id = _prepare_database(database_path)
    user = UserRepository(database_path).get_or_create_default_user()
    PreferencesRepository(database_path).upsert(
        user_id=user.id,
        desired_titles=[],
        seniority=[],
        technologies=[],
        work_modes=["remote"],
        locations=["Brazil"],
        required_terms=[],
        undesired_terms=["WordPress"],
    )
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(
                source_id=source_id,
                title="WordPress Developer",
                location="Brazil",
                work_mode="remote",
                content_hash="hash-1",
            ),
            _job(
                source_id=source_id,
                title="Frontend Developer",
                location="Brazil",
                work_mode="onsite",
                content_hash="hash-2",
            ),
            _job(
                source_id=source_id,
                title="React Developer",
                location="Remote Brazil",
                work_mode="remote",
                content_hash="hash-3",
            ),
        ]
    )

    summary = JobCleanupService(database_path).cleanup_jobs(today=date(2026, 6, 10))
    jobs = jobs_repository.list_all()

    assert summary.incompatible_jobs == 2
    assert jobs[0].status == "incompatible"
    assert jobs[1].status == "incompatible"
    assert jobs[2].status == "new"


def test_cleanup_keeps_brazilian_city_when_brazil_is_accepted(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    source_id = _prepare_database(database_path)
    user = UserRepository(database_path).get_or_create_default_user()
    PreferencesRepository(database_path).upsert(
        user_id=user.id,
        desired_titles=[],
        seniority=[],
        technologies=[],
        work_modes=["Remoto"],
        locations=["Brasil"],
        required_terms=[],
        undesired_terms=[],
    )
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            _job(
                source_id=source_id,
                title="React Developer",
                location="São Paulo, Brasil",
                work_mode="remote",
                content_hash="hash-1",
            ),
            _job(
                source_id=source_id,
                title="Frontend Developer",
                location="São Paulo",
                content_hash="hash-2",
            ),
        ]
    )

    summary = JobCleanupService(database_path).cleanup_jobs(today=date(2026, 6, 10))
    jobs = jobs_repository.list_all()

    assert summary.incompatible_jobs == 0
    assert jobs[0].status == "new"
    assert jobs[1].status == "new"


def _prepare_database(database_path: Path) -> int:
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    return sources_repository.list_all()[0].id


def _job(
    *,
    source_id: int,
    title: str,
    content_hash: str,
    company: str | None = None,
    location: str | None = None,
    work_mode: str | None = None,
    posted_at: str | None = None,
    job_url: str | None = None,
    email_message_id: int | None = None,
) -> Job:
    return Job(
        id=None,
        source_id=source_id,
        email_message_id=email_message_id,
        title=title,
        company=company,
        location=location,
        work_mode=work_mode,
        job_url=job_url,
        posted_at=posted_at,
        content_hash=content_hash,
    )
