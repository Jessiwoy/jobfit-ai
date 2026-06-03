from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import ProfileItem


class ProfileItemsRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list_by_user_id(self, user_id: int) -> list[ProfileItem]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    item_type,
                    name,
                    level,
                    years_experience,
                    evidence
                FROM profile_items
                WHERE user_id = ?
                ORDER BY item_type, name
                """,
                (user_id,),
            ).fetchall()

            return [
                ProfileItem(
                    id=row["id"],
                    user_id=row["user_id"],
                    item_type=row["item_type"],
                    name=row["name"],
                    level=row["level"],
                    years_experience=row["years_experience"],
                    evidence=row["evidence"],
                )
                for row in rows
            ]

    def replace_for_user(self, user_id: int, items: list[ProfileItem]) -> None:
        with connect(self._database_path) as connection:
            connection.execute("DELETE FROM profile_items WHERE user_id = ?", (user_id,))

            connection.executemany(
                """
                INSERT INTO profile_items (
                    user_id,
                    item_type,
                    name,
                    level,
                    years_experience,
                    evidence
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        user_id,
                        item.item_type,
                        item.name,
                        item.level,
                        item.years_experience,
                        item.evidence,
                    )
                    for item in items
                    if item.name.strip()
                ],
            )

