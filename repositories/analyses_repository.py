from __future__ import annotations

from pathlib import Path

from core.analysis_models import JobAnalysis
from core.database import connect

from repositories.json_fields import decode_string_list, encode_json


class AnalysesRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def upsert(self, analysis: JobAnalysis) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO job_analyses (
                    job_id,
                    score,
                    classification,
                    strengths,
                    gaps,
                    recommendation_reason,
                    matched_terms,
                    missing_terms,
                    undesired_terms_found
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    score = excluded.score,
                    classification = excluded.classification,
                    strengths = excluded.strengths,
                    gaps = excluded.gaps,
                    recommendation_reason = excluded.recommendation_reason,
                    matched_terms = excluded.matched_terms,
                    missing_terms = excluded.missing_terms,
                    undesired_terms_found = excluded.undesired_terms_found,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    analysis.job_id,
                    analysis.score,
                    analysis.classification,
                    encode_json(analysis.strengths),
                    encode_json(analysis.gaps),
                    analysis.recommendation_reason,
                    encode_json(analysis.matched_terms),
                    encode_json(analysis.missing_terms),
                    encode_json(analysis.undesired_terms_found),
                ),
            )

    def count_all(self) -> int:
        with connect(self._database_path) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM job_analyses").fetchone()

        return int(row["count"])

    def get_by_job_id(self, job_id: int) -> JobAnalysis | None:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    job_id,
                    score,
                    classification,
                    strengths,
                    gaps,
                    recommendation_reason,
                    matched_terms,
                    missing_terms,
                    undesired_terms_found
                FROM job_analyses
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_analysis(row)

    def list_by_job_ids(self, job_ids: list[int]) -> dict[int, JobAnalysis]:
        if not job_ids:
            return {}

        placeholders = ", ".join("?" for _ in job_ids)
        with connect(self._database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    job_id,
                    score,
                    classification,
                    strengths,
                    gaps,
                    recommendation_reason,
                    matched_terms,
                    missing_terms,
                    undesired_terms_found
                FROM job_analyses
                WHERE job_id IN ({placeholders})
                """,
                job_ids,
            ).fetchall()

        return {row["job_id"]: self._row_to_analysis(row) for row in rows}

    @staticmethod
    def _row_to_analysis(row) -> JobAnalysis:  # type: ignore[no-untyped-def]
        return JobAnalysis(
            id=row["id"],
            job_id=row["job_id"],
            score=row["score"],
            classification=row["classification"],
            strengths=decode_string_list(row["strengths"]),
            gaps=decode_string_list(row["gaps"]),
            recommendation_reason=row["recommendation_reason"],
            matched_terms=decode_string_list(row["matched_terms"]),
            missing_terms=decode_string_list(row["missing_terms"]),
            undesired_terms_found=decode_string_list(row["undesired_terms_found"]),
        )
