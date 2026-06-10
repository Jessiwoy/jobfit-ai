from pathlib import Path

from core.database import initialize_database
from core.models import Job, Preferences, ProfileItem
from repositories.analyses_repository import AnalysesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.profile_items_repository import ProfileItemsRepository
from repositories.user_repository import UserRepository
from services.scoring_service import ScoringService, build_job_analysis


def test_build_job_analysis_classifies_strong_match_as_apply() -> None:
    job = _job(
        job_id=1,
        title="React Frontend Developer",
        location="Remote Brazil",
        work_mode="remote",
        seniority="mid-level",
        description="React TypeScript dashboard role for remote teams.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Frontend Developer"],
        seniority=["mid-level"],
        technologies=["React", "TypeScript"],
        work_modes=["remote"],
        locations=["Brazil"],
        required_terms=["dashboard"],
        undesired_terms=["WordPress"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert analysis.score == 100
    assert analysis.classification == "Aplicar"
    assert "react" in analysis.matched_terms
    assert analysis.undesired_terms_found == []


def test_build_job_analysis_penalizes_undesired_terms() -> None:
    job = _job(
        job_id=1,
        title="Frontend Developer",
        description="Maintenance role with WordPress and PHP.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Frontend Developer"],
        technologies=["React"],
        undesired_terms=["WordPress", "PHP"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert analysis.classification == "Ignorar"
    assert analysis.undesired_terms_found == ["wordpress", "php"]


def test_scoring_service_saves_analysis_for_new_jobs(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    user = UserRepository(database_path).get_or_create_default_user()
    PreferencesRepository(database_path).upsert(
        user_id=user.id,
        desired_titles=["Frontend Developer"],
        seniority=[],
        technologies=["React"],
        work_modes=["remote"],
        locations=[],
        required_terms=[],
        undesired_terms=[],
    )
    ProfileItemsRepository(database_path).replace_for_user(
        user.id,
        [
            ProfileItem(
                id=None,
                user_id=user.id,
                item_type="technology",
                name="TypeScript",
            )
        ],
    )
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            Job(
                id=None,
                source_id=source.id,
                email_message_id=None,
                title="Frontend Developer",
                work_mode="remote",
                description="React TypeScript role.",
                content_hash="hash-1",
            )
        ]
    )

    summary = ScoringService(database_path).score_new_jobs()
    job = jobs_repository.list_all()[0]
    analysis = AnalysesRepository(database_path).get_by_job_id(job.id)

    assert summary.reviewed_jobs == 1
    assert summary.analyzed_jobs == 1
    assert analysis is not None
    assert analysis.score > 0
    assert analysis.classification in {"Aplicar", "Avaliar", "Ignorar"}


def test_scoring_service_skips_when_no_criteria_are_configured(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    JobsRepository(database_path).insert_many_ignore_existing(
        [
            Job(
                id=None,
                source_id=source.id,
                email_message_id=None,
                title="Frontend Developer",
                description="React role.",
                content_hash="hash-1",
            )
        ]
    )

    summary = ScoringService(database_path).score_new_jobs()

    assert summary.reviewed_jobs == 1
    assert summary.analyzed_jobs == 0
    assert summary.skipped_jobs == 1
    assert AnalysesRepository(database_path).count_all() == 0


def test_scoring_service_reports_empty_criteria_summary(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)

    summary = ScoringService(database_path).get_criteria_summary()

    assert summary.can_score is False
    assert summary.desired_titles == 0
    assert summary.profile_items == 0


def test_scoring_service_reports_configured_criteria_summary(tmp_path: Path) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    user = UserRepository(database_path).get_or_create_default_user()
    PreferencesRepository(database_path).upsert(
        user_id=user.id,
        desired_titles=["Frontend Developer"],
        seniority=["Pleno"],
        technologies=["React", "TypeScript"],
        work_modes=["Remoto"],
        locations=["Brasil"],
        required_terms=["Dashboard"],
        undesired_terms=["WordPress"],
    )
    ProfileItemsRepository(database_path).replace_for_user(
        user.id,
        [
            ProfileItem(
                id=None,
                user_id=user.id,
                item_type="technology",
                name="React",
            )
        ],
    )

    summary = ScoringService(database_path).get_criteria_summary()

    assert summary.can_score is True
    assert summary.desired_titles == 1
    assert summary.seniority == 1
    assert summary.technologies == 2
    assert summary.work_modes == 1
    assert summary.locations == 1
    assert summary.required_terms == 1
    assert summary.undesired_terms == 1
    assert summary.profile_items == 1


def _job(
    *,
    job_id: int,
    title: str,
    location: str | None = None,
    work_mode: str | None = None,
    seniority: str | None = None,
    description: str | None = None,
) -> Job:
    return Job(
        id=job_id,
        source_id=1,
        email_message_id=None,
        title=title,
        location=location,
        work_mode=work_mode,
        seniority=seniority,
        description=description,
        content_hash=f"hash-{job_id}",
    )
