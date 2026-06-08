from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository

from services.gmail_service import GmailCredentialsMissingError, GmailService


@dataclass(frozen=True)
class GmailSourceSyncResult:
    source_name: str
    label_name: str
    fetched_count: int
    inserted_count: int
    skipped_count: int
    error_message: str | None = None


@dataclass(frozen=True)
class GmailSyncSummary:
    results: list[GmailSourceSyncResult]

    @property
    def inserted_count(self) -> int:
        return sum(result.inserted_count for result in self.results)

    @property
    def fetched_count(self) -> int:
        return sum(result.fetched_count for result in self.results)

    @property
    def failed_count(self) -> int:
        return sum(1 for result in self.results if result.error_message)


class GmailSyncService:
    def __init__(
        self,
        database_path: Path,
        *,
        gmail_service: GmailService | None = None,
    ) -> None:
        self._sources_repository = JobSourcesRepository(database_path)
        self._messages_repository = EmailMessagesRepository(database_path)
        self._gmail_service = gmail_service or GmailService()

    def sync_active_sources(self, *, max_results_per_source: int = 25) -> GmailSyncSummary:
        self._sources_repository.ensure_default_sources()
        active_sources = [
            source for source in self._sources_repository.list_all() if source.enabled
        ]
        existing_ids = self._messages_repository.list_gmail_message_ids()
        results = []

        for source in active_sources:
            try:
                messages = self._gmail_service.fetch_messages_for_source(
                    source,
                    max_results=max_results_per_source,
                    existing_message_ids=existing_ids,
                )
                inserted_count = self._messages_repository.insert_many_ignore_existing(messages)
                self._sources_repository.mark_synced(source.id)
                existing_ids.update(message.gmail_message_id for message in messages)
                results.append(
                    GmailSourceSyncResult(
                        source_name=source.name,
                        label_name=source.gmail_label_name,
                        fetched_count=len(messages),
                        inserted_count=inserted_count,
                        skipped_count=len(messages) - inserted_count,
                    )
                )
            except GmailCredentialsMissingError:
                raise
            except Exception as error:
                results.append(
                    GmailSourceSyncResult(
                        source_name=source.name,
                        label_name=source.gmail_label_name,
                        fetched_count=0,
                        inserted_count=0,
                        skipped_count=0,
                        error_message=str(error),
                    )
                )

        return GmailSyncSummary(results=results)
