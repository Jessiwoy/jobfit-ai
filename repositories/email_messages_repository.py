from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import EmailMessage


class EmailMessagesRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def exists_by_gmail_message_id(self, gmail_message_id: str) -> bool:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM email_messages
                WHERE gmail_message_id = ?
                LIMIT 1
                """,
                (gmail_message_id,),
            ).fetchone()

        return row is not None

    def list_gmail_message_ids(self) -> set[str]:
        with connect(self._database_path) as connection:
            rows = connection.execute("SELECT gmail_message_id FROM email_messages").fetchall()

        return {str(row["gmail_message_id"]) for row in rows}

    def insert_many_ignore_existing(self, messages: list[EmailMessage]) -> int:
        if not messages:
            return 0

        with connect(self._database_path) as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO email_messages (
                    source_id,
                    gmail_message_id,
                    gmail_thread_id,
                    gmail_label_name,
                    subject,
                    sender,
                    received_at,
                    raw_text,
                    raw_html,
                    detected_provider,
                    processed_status,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        message.source_id,
                        message.gmail_message_id,
                        message.gmail_thread_id,
                        message.gmail_label_name,
                        message.subject,
                        message.sender,
                        message.received_at,
                        message.raw_text,
                        message.raw_html,
                        message.detected_provider,
                        message.processed_status,
                        message.error_message,
                    )
                    for message in messages
                ],
            )
            return connection.total_changes - before

    def count_all(self) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM email_messages").fetchone()

        return int(row["count"])

    def list_recent(self, limit: int = 20) -> list[EmailMessage]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    gmail_message_id,
                    gmail_thread_id,
                    gmail_label_name,
                    subject,
                    sender,
                    received_at,
                    raw_text,
                    raw_html,
                    detected_provider,
                    processed_status,
                    error_message
                FROM email_messages
                ORDER BY COALESCE(received_at, created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            EmailMessage(
                id=row["id"],
                source_id=row["source_id"],
                gmail_message_id=row["gmail_message_id"],
                gmail_thread_id=row["gmail_thread_id"],
                gmail_label_name=row["gmail_label_name"],
                subject=row["subject"],
                sender=row["sender"],
                received_at=row["received_at"],
                raw_text=row["raw_text"],
                raw_html=row["raw_html"],
                detected_provider=row["detected_provider"],
                processed_status=row["processed_status"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    def list_by_status(self, status: str, *, limit: int = 50) -> list[EmailMessage]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    gmail_message_id,
                    gmail_thread_id,
                    gmail_label_name,
                    subject,
                    sender,
                    received_at,
                    raw_text,
                    raw_html,
                    detected_provider,
                    processed_status,
                    error_message
                FROM email_messages
                WHERE processed_status = ?
                ORDER BY COALESCE(received_at, created_at) DESC
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()

        return [
            EmailMessage(
                id=row["id"],
                source_id=row["source_id"],
                gmail_message_id=row["gmail_message_id"],
                gmail_thread_id=row["gmail_thread_id"],
                gmail_label_name=row["gmail_label_name"],
                subject=row["subject"],
                sender=row["sender"],
                received_at=row["received_at"],
                raw_text=row["raw_text"],
                raw_html=row["raw_html"],
                detected_provider=row["detected_provider"],
                processed_status=row["processed_status"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    def count_by_status(self, status: str) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM email_messages
                WHERE processed_status = ?
                """,
                (status,),
            ).fetchone()

        return int(row["count"])

    def mark_processed(self, message_id: int) -> None:
        self._update_status(message_id, "processed", None)

    def mark_failed(self, message_id: int, error_message: str) -> None:
        self._update_status(message_id, "error", error_message)

    def _update_status(
        self,
        message_id: int,
        status: str,
        error_message: str | None,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE email_messages
                SET processed_status = ?,
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, error_message, message_id),
            )
