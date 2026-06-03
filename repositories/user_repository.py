from __future__ import annotations

from pathlib import Path

from core.database import connect
from core.models import User


class UserRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def get_or_create_default_user(self) -> User:
        with connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT id, name, email, current_title, location, summary
                FROM users
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                cursor = connection.execute("INSERT INTO users DEFAULT VALUES")
                user_id = int(cursor.lastrowid)
                return User(id=user_id)

            return self._row_to_user(row)

    def update_profile(
        self,
        *,
        user_id: int,
        name: str,
        email: str,
        current_title: str,
        location: str,
        summary: str,
    ) -> None:
        with connect(self._database_path) as connection:
            connection.execute(
                """
                UPDATE users
                SET
                    name = ?,
                    email = ?,
                    current_title = ?,
                    location = ?,
                    summary = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, email, current_title, location, summary, user_id),
            )

    @staticmethod
    def _row_to_user(row) -> User:  # type: ignore[no-untyped-def]
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            current_title=row["current_title"],
            location=row["location"],
            summary=row["summary"],
        )

