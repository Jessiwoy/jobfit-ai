from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import JobSource

DEFAULT_SOURCES = [
    {
        "name": "Job Alerts",
        "gmail_label_name": "Job Alerts",
        "parser_type": "generic",
    },
]

LEGACY_DEFAULT_LABELS = {"Linkedin Jobs", "Indeed Jobs"}
LEGACY_SINGLE_LABELS = {"job-alerts"}


class JobSourcesRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def ensure_default_sources(self) -> None:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                "SELECT name, gmail_label_name FROM job_sources ORDER BY name"
            ).fetchall()

            existing_labels = {row["gmail_label_name"] for row in rows}
            if existing_labels in (LEGACY_DEFAULT_LABELS, LEGACY_SINGLE_LABELS):
                connection.execute("DELETE FROM job_sources")

            for source in DEFAULT_SOURCES:
                connection.execute(
                    """
                    INSERT INTO job_sources (
                        name,
                        gmail_label_name,
                        parser_type
                    )
                    VALUES (?, ?, ?)
                    ON CONFLICT(name) DO NOTHING
                    """,
                    (
                        source["name"],
                        source["gmail_label_name"],
                        source["parser_type"],
                    ),
                )

    def list_all(self) -> list[JobSource]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, name, gmail_label_name, source_type, parser_type, enabled
                FROM job_sources
                ORDER BY name
                """
            ).fetchall()

            return [
                JobSource(
                    id=row["id"],
                    name=row["name"],
                    gmail_label_name=row["gmail_label_name"],
                    source_type=row["source_type"],
                    parser_type=row["parser_type"],
                    enabled=bool(row["enabled"]),
                )
                for row in rows
            ]

    def replace_all(self, sources: list[JobSource]) -> None:
        with connect(self._database_path) as connection:
            connection.execute("DELETE FROM job_sources")

            connection.executemany(
                """
                INSERT INTO job_sources (
                    name,
                    gmail_label_name,
                    source_type,
                    parser_type,
                    enabled
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        source.name,
                        source.gmail_label_name,
                        source.source_type,
                        source.parser_type,
                        int(source.enabled),
                    )
                    for source in sources
                    if source.name.strip() and source.gmail_label_name.strip()
                ],
            )

    def mark_synced(self, source_id: int) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE job_sources
                SET last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (source_id,),
            )
