from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from core.config import DATABASE_PATH, MIGRATIONS_DIR


def get_database_path() -> Path:
    return DATABASE_PATH


def connect(database_path: Path | None = None) -> sqlite3.Connection:
    path = database_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | None = None) -> None:
    with connect(database_path) as connection:
        _ensure_migrations_table(connection)
        applied = _get_applied_migrations(connection)

        for migration_file in _iter_migration_files():
            if migration_file.name in applied:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            connection.executescript(sql)
            connection.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (migration_file.name,),
            )


def _ensure_migrations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _get_applied_migrations(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def _iter_migration_files() -> Iterable[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"))

