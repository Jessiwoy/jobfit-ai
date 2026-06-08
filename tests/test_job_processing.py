from pathlib import Path

from core.database import initialize_database
from core.models import EmailMessage
from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository
from services.job_processing_service import NO_JOBS_EXTRACTED_ERROR, JobProcessingService


def test_job_processing_creates_jobs_from_new_emails(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    messages_repository = EmailMessagesRepository(database_path)
    jobs_repository = JobsRepository(database_path)

    messages_repository.insert_many_ignore_existing(
        [
            EmailMessage(
                id=None,
                source_id=source.id,
                gmail_message_id="msg-1",
                gmail_thread_id="thread-1",
                gmail_label_name=source.gmail_label_name,
                subject="Frontend Developer at Acme",
                raw_text="Location: Remote Brazil\nhttps://example.com/job",
                detected_provider="linkedin",
            )
        ]
    )

    summary = JobProcessingService(database_path).process_new_messages(limit=10)

    assert summary.processed_messages == 1
    assert summary.created_jobs == 1
    assert summary.failed_messages == 0
    assert messages_repository.count_by_status("processed") == 1
    assert jobs_repository.count_all() == 1
    assert jobs_repository.list_recent()[0].title == "Frontend Developer at Acme"


def test_job_processing_does_not_duplicate_existing_jobs(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    messages_repository = EmailMessagesRepository(database_path)

    messages_repository.insert_many_ignore_existing(
        [
            EmailMessage(
                id=None,
                source_id=source.id,
                gmail_message_id="msg-1",
                gmail_thread_id="thread-1",
                gmail_label_name=source.gmail_label_name,
                subject="Frontend Developer at Acme",
                raw_text="Remote\nhttps://example.com/job",
            ),
            EmailMessage(
                id=None,
                source_id=source.id,
                gmail_message_id="msg-2",
                gmail_thread_id="thread-2",
                gmail_label_name=source.gmail_label_name,
                subject="Frontend Developer at Acme",
                raw_text="Remote\nhttps://example.com/job",
            ),
        ]
    )

    summary = JobProcessingService(database_path).process_new_messages(limit=10)

    assert summary.processed_messages == 2
    assert summary.created_jobs == 1
    assert JobsRepository(database_path).count_all() == 1


def test_job_processing_marks_email_as_error_when_no_job_is_extracted(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    messages_repository = EmailMessagesRepository(database_path)

    messages_repository.insert_many_ignore_existing(
        [
            EmailMessage(
                id=None,
                source_id=source.id,
                gmail_message_id="msg-1",
                gmail_thread_id="thread-1",
                gmail_label_name=source.gmail_label_name,
            )
        ]
    )

    summary = JobProcessingService(database_path).process_new_messages(limit=10)
    failed_message = messages_repository.list_by_status("error")[0]

    assert summary.processed_messages == 1
    assert summary.created_jobs == 0
    assert summary.failed_messages == 1
    assert failed_message.error_message == NO_JOBS_EXTRACTED_ERROR
