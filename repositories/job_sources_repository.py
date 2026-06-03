from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import JobSource

DEFAULT_SOURCES = [
    {
        "name": "LinkedIn",
        "gmail_label_name": "Linkedin Jobs",
        "parser_type": "linkedin",
    },
    {
        "name": "Indeed",
        "gmail_label_name": "Indeed Jobs",
        "parser_type": "indeed",
    },
]


class JobSourcesRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def ensure_default_sources(self) -> None:
        with connect(self._database_path) as connection:
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

