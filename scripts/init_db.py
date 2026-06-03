from __future__ import annotations

from core.database import get_database_path, initialize_database
from repositories.job_sources_repository import JobSourcesRepository
from repositories.user_repository import UserRepository


def main() -> None:
    initialize_database()
    database_path = get_database_path()
    UserRepository(database_path).get_or_create_default_user()
    JobSourcesRepository(database_path).ensure_default_sources()
    print(f"Banco inicializado em: {database_path}")


if __name__ == "__main__":
    main()

