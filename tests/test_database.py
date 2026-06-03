from pathlib import Path

from core.database import initialize_database
from core.models import JobSource, ProfileItem
from repositories.job_sources_repository import JobSourcesRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.profile_items_repository import ProfileItemsRepository
from repositories.user_repository import UserRepository


def test_initialize_database_creates_core_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"

    initialize_database(database_path)

    user = UserRepository(database_path).get_or_create_default_user()
    assert user.id == 1


def test_default_job_sources_are_created_once(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    repository = JobSourcesRepository(database_path)

    repository.ensure_default_sources()
    repository.ensure_default_sources()

    sources = repository.list_all()

    assert len(sources) == 2
    assert {source.gmail_label_name for source in sources} == {"Linkedin Jobs", "Indeed Jobs"}


def test_job_sources_can_be_replaced(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    repository = JobSourcesRepository(database_path)
    repository.ensure_default_sources()

    repository.replace_all(
        [
            JobSource(
                id=0,
                name="Custom",
                gmail_label_name="Custom Jobs",
                source_type="gmail_label",
                parser_type="generic",
                enabled=True,
            ),
            JobSource(
                id=0,
                name="Disabled",
                gmail_label_name="Disabled Jobs",
                source_type="gmail_label",
                parser_type="generic",
                enabled=False,
            ),
        ]
    )

    sources = repository.list_all()

    assert {source.name for source in sources} == {"Custom", "Disabled"}
    assert {source.gmail_label_name for source in sources} == {"Custom Jobs", "Disabled Jobs"}
    assert any(not source.enabled for source in sources)


def test_preferences_can_be_saved_and_loaded(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    user = UserRepository(database_path).get_or_create_default_user()
    repository = PreferencesRepository(database_path)

    repository.upsert(
        user_id=user.id,
        desired_titles=["Frontend Developer", "Full Stack Developer"],
        seniority=["Junior", "Mid-level"],
        technologies=["React", "TypeScript"],
        work_modes=["Remote", "Hybrid"],
        locations=["Brazil"],
        required_terms=["React"],
        undesired_terms=["PHP", "WordPress"],
    )

    preferences = repository.get_by_user_id(user.id)

    assert preferences.desired_titles == ["Frontend Developer", "Full Stack Developer"]
    assert preferences.technologies == ["React", "TypeScript"]
    assert preferences.undesired_terms == ["PHP", "WordPress"]


def test_profile_items_can_be_replaced_for_user(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    user = UserRepository(database_path).get_or_create_default_user()
    repository = ProfileItemsRepository(database_path)

    repository.replace_for_user(
        user.id,
        [
            ProfileItem(
                id=None,
                user_id=user.id,
                item_type="technology",
                name="React",
                level="Intermediate",
                years_experience=1.5,
                evidence="Built dashboard interfaces.",
            ),
            ProfileItem(
                id=None,
                user_id=user.id,
                item_type="project",
                name="Taskly",
                evidence="React Native task management app.",
            ),
        ],
    )

    repository.replace_for_user(
        user.id,
        [
            ProfileItem(
                id=None,
                user_id=user.id,
                item_type="technology",
                name="TypeScript",
                evidence="Used across web and mobile applications.",
            ),
        ],
    )

    items = repository.list_by_user_id(user.id)

    assert len(items) == 1
    assert items[0].name == "TypeScript"
    assert items[0].item_type == "technology"
