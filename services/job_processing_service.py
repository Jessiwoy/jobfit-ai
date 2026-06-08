from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repositories.email_messages_repository import EmailMessagesRepository
from repositories.jobs_repository import JobsRepository

from services.email_parser import GenericEmailParser


@dataclass(frozen=True)
class JobProcessingSummary:
    processed_messages: int
    created_jobs: int
    failed_messages: int


class JobProcessingService:
    def __init__(self, database_path: Path) -> None:
        self._messages_repository = EmailMessagesRepository(database_path)
        self._jobs_repository = JobsRepository(database_path)
        self._parser = GenericEmailParser()

    def process_new_messages(self, *, limit: int = 50) -> JobProcessingSummary:
        messages = self._messages_repository.list_by_status("new", limit=limit)
        created_jobs = 0
        failed_messages = 0

        for message in messages:
            if message.id is None:
                continue

            try:
                jobs = self._parser.parse(message)
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
