from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository

from services.parsers import select_email_parser

NO_JOBS_EXTRACTED_ERROR = "Nenhuma vaga foi extraida do e-mail."


@dataclass(frozen=True)
class JobProcessingSummary:
    processed_messages: int
    created_jobs: int
    failed_messages: int


class JobProcessingService:
    def __init__(self, database_path: Path) -> None:
        self._messages_repository = EmailMessagesRepository(database_path)
        self._sources_repository = JobSourcesRepository(database_path)
        self._jobs_repository = JobsRepository(database_path)

    def process_new_messages(self, *, limit: int = 50) -> JobProcessingSummary:
        return self._process_messages_by_status("new", limit=limit)

    def reprocess_failed_messages(self, *, limit: int = 50) -> JobProcessingSummary:
        return self._process_messages_by_status("error", limit=limit)

    def _process_messages_by_status(self, status: str, *, limit: int) -> JobProcessingSummary:
        messages = self._messages_repository.list_by_status(status, limit=limit)
        sources_by_id = {source.id: source for source in self._sources_repository.list_all()}
        created_jobs = 0
        failed_messages = 0

        for message in messages:
            if message.id is None:
                continue

            try:
                parser = select_email_parser(message, sources_by_id.get(message.source_id))
                jobs = parser.parse(message)
                if not jobs:
                    failed_messages += 1
                    self._messages_repository.mark_failed(message.id, NO_JOBS_EXTRACTED_ERROR)
                    continue

                created_jobs += self._jobs_repository.insert_many_ignore_existing(jobs)
                self._messages_repository.mark_processed(message.id)
            except Exception as error:
                failed_messages += 1
                self._messages_repository.mark_failed(message.id, str(error))

        return JobProcessingSummary(
            processed_messages=len(messages),
            created_jobs=created_jobs,
            failed_messages=failed_messages,
        )
