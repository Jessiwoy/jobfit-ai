from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import Job


class JobsRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def insert_many_ignore_existing(self, jobs: list[Job]) -> int:
        if not jobs:
            return 0

        with connect(self._database_path) as connection:
            before = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO jobs (
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        job.source_id,
                        job.email_message_id,
                        job.title,
                        job.company,
                        job.location,
                        job.work_mode,
                        job.seniority,
                        job.job_url,
                        job.description,
                        job.posted_at,
                        job.source_job_id,
                        job.content_hash,
                        job.status,
                        job.provider,
                    )
                    for job in jobs
                ],
            )
            return connection.total_changes - before

    def count_all(self) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()

        return int(row["count"])

    def count_by_status(self, status: str) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM jobs WHERE status = ?",
                (status,),
            ).fetchone()

        return int(row["count"])

    def list_all(self) -> list[Job]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider,
                    application_status,
                    applied_at,
                    created_at
                FROM jobs
                ORDER BY id
                """
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def list_recent(self, limit: int = 50, statuses: list[str] | None = None) -> list[Job]:
        if statuses == []:
            return []

        status_filter = ""
        parameters: list[object] = []

        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            status_filter = f"WHERE status IN ({placeholders})"
            parameters.extend(statuses)

        parameters.append(limit)

        with connect(self._database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider,
                    application_status,
                    applied_at,
                    created_at
                FROM jobs
                {status_filter}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def list_recent_unapplied(self, limit: int = 50) -> list[Job]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider,
                    application_status,
                    applied_at,
                    created_at
                FROM jobs
                WHERE application_status NOT IN ('applied', 'archived', 'not_tracking')
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def get_by_id(self, job_id: int) -> Job | None:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider,
                    application_status,
                    applied_at,
                    created_at
                FROM jobs
                WHERE id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def list_applied(self, limit: int = 500) -> list[Job]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    email_message_id,
                    title,
                    company,
                    location,
                    work_mode,
                    seniority,
                    job_url,
                    description,
                    posted_at,
                    source_job_id,
                    content_hash,
                    status,
                    provider,
                    application_status,
                    applied_at,
                    created_at
                FROM jobs
                WHERE application_status = 'applied'
                ORDER BY COALESCE(applied_at, updated_at, created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def update_status(self, job_id: int, status: str) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE jobs
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, job_id),
            )

    def update_description(self, job_id: int, description: str) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE jobs
                SET description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (description, job_id),
            )

    def update_application_status(self, job_id: int, application_status: str) -> None:
        applied_at_expression = (
            "CURRENT_TIMESTAMP" if application_status == "applied" else "NULL"
        )
        with connect(self._database_path) as connection:
            connection.execute(
                f"""
                UPDATE jobs
                SET application_status = ?,
                    applied_at = {applied_at_expression},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (application_status, job_id),
            )

    def update_details_from_page(
        self,
        job_id: int,
        *,
        title: str | None,
        company: str | None,
        location: str | None,
        posted_at: str | None,
        description: str,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE jobs
                SET title = COALESCE(NULLIF(?, ''), title),
                    company = COALESCE(NULLIF(?, ''), company),
                    location = COALESCE(NULLIF(?, ''), location),
                    posted_at = COALESCE(NULLIF(?, ''), posted_at),
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, company, location, posted_at, description, job_id),
            )

    @staticmethod
    def _row_to_job(row) -> Job:  # type: ignore[no-untyped-def]
        job_data = {
            "id": row["id"],
            "source_id": row["source_id"],
            "email_message_id": row["email_message_id"],
            "title": row["title"],
            "company": row["company"],
            "location": row["location"],
            "work_mode": row["work_mode"],
            "seniority": row["seniority"],
            "job_url": row["job_url"],
            "description": row["description"],
            "posted_at": row["posted_at"],
            "source_job_id": row["source_job_id"],
            "content_hash": row["content_hash"],
            "status": row["status"],
            "provider": row["provider"],
            "application_status": row["application_status"],
            "applied_at": row["applied_at"],
            "created_at": row["created_at"],
        }
        try:
            return Job(**job_data)
        except TypeError:
            job_data.pop("application_status")
            job_data.pop("applied_at")
            job_data.pop("created_at")
            return Job(**job_data)
