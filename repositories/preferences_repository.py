from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import Preferences

from repositories.json_fields import decode_string_list, encode_json


class PreferencesRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def get_by_user_id(self, user_id: int) -> Preferences:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    desired_titles,
                    seniority,
                    technologies,
                    work_modes,
                    locations,
                    required_terms,
                    undesired_terms
                FROM preferences
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

            if row is None:
                return Preferences(id=None, user_id=user_id)

            return Preferences(
                id=row["id"],
                user_id=row["user_id"],
                desired_titles=decode_string_list(row["desired_titles"]),
                seniority=decode_string_list(row["seniority"]),
                technologies=decode_string_list(row["technologies"]),
                work_modes=decode_string_list(row["work_modes"]),
                locations=decode_string_list(row["locations"]),
                required_terms=decode_string_list(row["required_terms"]),
                undesired_terms=decode_string_list(row["undesired_terms"]),
            )

    def upsert(
        self,
        *,
        user_id: int,
        desired_titles: list[str],
        seniority: list[str],
        technologies: list[str],
        work_modes: list[str],
        locations: list[str],
        required_terms: list[str],
        undesired_terms: list[str],
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO preferences (
                    user_id,
                    desired_titles,
                    seniority,
                    technologies,
                    work_modes,
                    locations,
                    required_terms,
                    undesired_terms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    desired_titles = excluded.desired_titles,
                    seniority = excluded.seniority,
                    technologies = excluded.technologies,
                    work_modes = excluded.work_modes,
                    locations = excluded.locations,
                    required_terms = excluded.required_terms,
                    undesired_terms = excluded.undesired_terms,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    encode_json(desired_titles),
                    encode_json(seniority),
                    encode_json(technologies),
                    encode_json(work_modes),
                    encode_json(locations),
                    encode_json(required_terms),
                    encode_json(undesired_terms),
                ),
            )

