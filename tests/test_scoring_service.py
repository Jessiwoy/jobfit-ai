from pathlib import Path
from types import SimpleNamespace

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

    assert analysis.score >= 80
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


def test_build_job_analysis_matches_common_portuguese_variants() -> None:
    job = _job(
        job_id=1,
        title="Desenvolvedor React Junior - Trabalho Remoto",
        location="Brasil",
        work_mode="remote",
        seniority="junior",
        description="Vaga front-end com React.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Desenvolvedora React"],
        seniority=["Júnior"],
        technologies=["Frontend", "React"],
        work_modes=["Remoto"],
        locations=["Brasil"],
        required_terms=["React"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert analysis.score >= 80
    assert analysis.classification == "Aplicar"


def test_build_job_analysis_does_not_require_every_configured_technology() -> None:
    job = _job(
        job_id=1,
        title="Desenvolvedor React Junior - Trabalho Remoto",
        location="São Paulo, Brasil",
        work_mode="remote",
        seniority="junior",
        description="ReactJS em produto web.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=[
            "Desenvolvedora Frontend",
            "Desenvolvedor React",
            "Full Stack Developer",
        ],
        seniority=["Junior", "Pleno"],
        technologies=[
            "React",
            "TypeScript",
            "JavaScript",
            "Node",
            "Nest",
            "Prisma",
            "Vite",
            "AWS",
            "HTML",
            "CSS",
            "Frontend",
            "Full Stack",
        ],
        work_modes=["Remoto"],
        locations=["Brasil"],
        required_terms=["React"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert analysis.score >= 80
    assert analysis.classification == "Aplicar"


def test_build_job_analysis_rewards_resume_evidence_context() -> None:
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
    profile_items = [
        ProfileItem(
            id=None,
            user_id=1,
            item_type="technology",
            name="React",
            evidence="Built production dashboards with React and TypeScript.",
        ),
        ProfileItem(
            id=None,
            user_id=1,
            item_type="project",
            name="TypeScript dashboard",
            evidence="Consumed REST APIs for remote product teams.",
        ),
    ]

    analysis = build_job_analysis(job, preferences, profile_items)

    assert analysis.score == 100
    assert analysis.classification == "Aplicar"
    assert "react" in analysis.matched_terms


def test_build_job_analysis_classifies_score_70_as_apply() -> None:
    job = _job(
        job_id=1,
        title="React Developer",
        work_mode="remote",
        description="React TypeScript role.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["React Developer"],
        technologies=["React", "TypeScript"],
        work_modes=["remote"],
        required_terms=["React"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert analysis.score == 70
    assert analysis.classification == "Aplicar"


def test_build_job_analysis_rewards_transferable_frontend_and_backend_skills() -> None:
    job = _job(
        job_id=1,
        title="Profissional de Desenvolvimento Fullstack Junior",
        location="Brasil",
        seniority="junior",
        description=(
            "Vaga full stack com Angular ou outro framework frontend, "
            "Python, APIs REST, HTML e CSS."
        ),
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Desenvolvedor Full Stack"],
        seniority=["Junior"],
        technologies=["React", "TypeScript", "JavaScript", "Node", "APIs REST"],
        locations=["Brasil"],
    )
    profile_items = [
        ProfileItem(
            id=None,
            user_id=1,
            item_type="technology",
            name="React",
            evidence="Construi interfaces React com TypeScript consumindo APIs REST.",
        ),
        ProfileItem(
            id=None,
            user_id=1,
            item_type="technology",
            name="Node",
            evidence="Integrei backend e APIs usando JavaScript e Node.",
        ),
        ProfileItem(
            id=None,
            user_id=1,
            item_type="skill",
            name="Full Stack",
        ),
    ]

    analysis = build_job_analysis(job, preferences, profile_items)

    assert analysis.score >= 70
    assert analysis.classification == "Aplicar"
    assert "angular" in analysis.matched_terms
    assert "python" in analysis.matched_terms


def test_build_job_analysis_does_not_match_short_terms_inside_tracking_tokens() -> None:
    job = _job(
        job_id=1,
        title="Profissional de Desenvolvimento Fullstack Junior",
        description="https://www.linkedin.com/jobs/view/123?lipi=Z2e8VZlBSEOOSILsr8gFVA",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Desenvolvedor Full Stack"],
        technologies=["SEO"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert "seo" not in analysis.matched_terms


def test_build_job_analysis_handles_sparse_fullstack_linkedin_alert() -> None:
    job = _job(
        job_id=1,
        title="Profissional de Desenvolvimento Fullstack Junior",
        location="Brasil",
        seniority="junior",
        description=(
            "Profissional de Desenvolvimento Fullstack Junior\n"
            "Radix\n"
            "Brasil\n"
            "https://www.linkedin.com/jobs/view/4417966383/?lipi=Z2e8VZlBSEOOSILsr8gFVA"
        ),
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Full Stack Developer", "Desenvolvedor Full Stack"],
        seniority=["Junior", "Pleno"],
        technologies=["React", "TypeScript", "JavaScript", "Node", "Full Stack"],
        locations=["Brasil"],
    )
    profile_items = [
        ProfileItem(
            id=None,
            user_id=1,
            item_type="technology",
            name="React",
        )
    ]

    analysis = build_job_analysis(job, preferences, profile_items)

    assert analysis.score >= 60
    assert "seo" not in analysis.matched_terms
    assert "full stack" in analysis.matched_terms
    assert "full stack developer" not in analysis.missing_terms


def test_missing_terms_only_reports_unconfirmed_scoring_categories() -> None:
    job = _job(
        job_id=1,
        title="Desenvolvedor Frontend Junior",
        location="Brasil",
        seniority="junior",
        description="Vaga com React.",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Desenvolvedor Frontend", "Desenvolvedor Full Stack"],
        seniority=["Junior", "Pleno"],
        technologies=["React", "TypeScript", "Node"],
        locations=["Brasil", "Santa Catarina"],
        required_terms=["React"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert "desenvolvedor full stack" not in analysis.missing_terms
    assert "typescript" not in analysis.missing_terms
    assert "pleno" not in analysis.missing_terms
    assert "santa catarina" not in analysis.missing_terms


def test_title_matching_does_not_treat_frontend_and_fullstack_as_the_same_role() -> None:
    job = _job(
        job_id=1,
        title="Profissional de Desenvolvimento Fullstack Junior",
        seniority="junior",
    )
    preferences = Preferences(
        id=None,
        user_id=1,
        desired_titles=["Frontend Developer"],
        seniority=["Junior"],
    )

    analysis = build_job_analysis(job, preferences, [])

    assert "frontend desenvolvedor" not in analysis.matched_terms
    assert analysis.score == 10


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


def test_scoring_service_enriches_descriptions_before_scoring(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
        technologies=["React", "TypeScript"],
        work_modes=[],
        locations=[],
        required_terms=[],
        undesired_terms=[],
    )
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
        [
            Job(
                id=None,
                source_id=source.id,
                email_message_id=None,
                title="Frontend Developer",
                job_url="https://example.com/jobs/frontend",
                description="Resumo curto do email.",
                content_hash="hash-1",
            )
        ]
    )

    class FakeEnrichmentService:
        def __init__(self, database_path: Path, *, cdp_url: str | None = None) -> None:
            self._jobs_repository = JobsRepository(database_path)

        def enrich_jobs(self, jobs: list[Job]) -> SimpleNamespace:
            for job in jobs:
                assert job.id is not None
                self._jobs_repository.update_description(
                    job.id,
                    "Descricao completa com requisitos React e TypeScript.",
                )
            return SimpleNamespace(
                attempted_jobs=len(jobs),
                enriched_jobs=len(jobs),
                failed_jobs=0,
                errors=[],
            )

    monkeypatch.setattr(
        "services.scoring_service.JobDescriptionEnrichmentService",
        FakeEnrichmentService,
    )

    summary = ScoringService(database_path).score_new_jobs(enrich_descriptions=True)
    job = jobs_repository.list_all()[0]
    analysis = AnalysesRepository(database_path).get_by_job_id(job.id)

    assert summary.enrichment_attempted_jobs == 1
    assert summary.enriched_jobs == 1
    assert analysis is not None
    assert analysis.score > 0
    assert "react" in analysis.matched_terms
    assert "typescript" in analysis.matched_terms


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


def test_scoring_service_clears_existing_analyses_when_no_criteria_are_configured(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "jobfit.db"
    initialize_database(database_path)
    sources_repository = JobSourcesRepository(database_path)
    sources_repository.ensure_default_sources()
    source = sources_repository.list_all()[0]
    jobs_repository = JobsRepository(database_path)
    jobs_repository.insert_many_ignore_existing(
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
    job = jobs_repository.list_all()[0]
    analyses_repository = AnalysesRepository(database_path)
    analyses_repository.upsert(
        build_job_analysis(
            job,
            Preferences(
                id=None,
                user_id=1,
                desired_titles=["Frontend Developer"],
            ),
            [],
        )
    )

    summary = ScoringService(database_path).score_new_jobs()

    assert summary.reviewed_jobs == 1
    assert summary.analyzed_jobs == 0
    assert summary.skipped_jobs == 1
    assert summary.cleared_analyses == 1
    assert analyses_repository.count_all() == 0


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
