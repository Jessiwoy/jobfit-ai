from pathlib import Path

from core.database import initialize_database
from core.models import EmailMessage, JobSource
from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository
from services.gmail_sync_service import GmailSyncService


class FakeGmailService:
    def fetch_messages_for_source(
        self,
        source: JobSource,
        *,
        max_results: int,
        existing_message_ids: set[str] | None = None,
    ) -> list[EmailMessage]:
        if existing_message_ids and "msg-1" in existing_message_ids:
            return []

        return [
            EmailMessage(
                id=None,
                source_id=source.id,
                gmail_message_id="msg-1",
                gmail_thread_id="thread-1",
                gmail_label_name=source.gmail_label_name,
                subject="Frontend Developer",
                sender="jobs@example.com",
                raw_text="React TypeScript remote job",
                detected_provider="linkedin",
            )
        ][:max_results]


def test_email_messages_repository_inserts_and_ignores_duplicates(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    repository = EmailMessagesRepository(database_path)
    message = EmailMessage(
        id=None,
        source_id=source.id,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name=source.gmail_label_name,
        subject="Frontend Developer",
    )

    assert repository.insert_many_ignore_existing([message]) == 1
    assert repository.insert_many_ignore_existing([message]) == 0
    assert repository.count_all() == 1
    assert repository.list_gmail_message_ids() == {"msg-1"}


def test_gmail_sync_saves_only_new_messages(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sync_service = GmailSyncService(
        database_path,
        gmail_service=FakeGmailService(),  # type: ignore[arg-type]
    )

    first_summary = sync_service.sync_active_sources(max_results_per_source=25)
    second_summary = sync_service.sync_active_sources(max_results_per_source=25)

    assert first_summary.inserted_count == 1
    assert first_summary.fetched_count == 1
    assert second_summary.inserted_count == 0
    assert second_summary.fetched_count == 0
    assert EmailMessagesRepository(database_path).count_all() == 1
