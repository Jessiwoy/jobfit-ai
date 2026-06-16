from datetime import date

from app.streamlit_app import (
    build_dashboard_summary_row,
    filter_dashboard_jobs,
    is_dashboard_candidate,
    list_recent_dashboard_jobs,
    matches_imported_date_filter,
)
from core.analysis_models import JobAnalysis
from core.models import Job


def test_filter_dashboard_jobs_keeps_unscored_jobs_when_selected() -> None:
    jobs = [_job(1), _job(2)]
    analyses = {
        2: JobAnalysis(
            id=1,
            job_id=2,
            score=80,
            classification="Aplicar",
        )
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=0,
        selected_classifications=["Sem score", "Aplicar"],
    )

    assert [job.id for job in filtered_jobs] == [1, 2]


def test_filter_dashboard_jobs_keeps_only_unscored_jobs_when_only_sem_score_selected() -> None:
    jobs = [_job(1), _job(2)]
    analyses = {
        2: JobAnalysis(
            id=1,
            job_id=2,
            score=80,
            classification="Aplicar",
        )
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=0,
        selected_classifications=["Sem score"],
    )

    assert [job.id for job in filtered_jobs] == [1]


def test_filter_dashboard_jobs_keeps_unscored_jobs_even_with_minimum_score() -> None:
    jobs = [_job(1), _job(2)]
    analyses = {
        2: JobAnalysis(
            id=1,
            job_id=2,
            score=40,
            classification="Ignorar",
        )
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=60,
        selected_classifications=["Sem score"],
    )

    assert [job.id for job in filtered_jobs] == [1]


def test_filter_dashboard_jobs_applies_score_and_classification() -> None:
    jobs = [_job(1), _job(2), _job(3)]
    analyses = {
        1: JobAnalysis(id=1, job_id=1, score=90, classification="Aplicar"),
        2: JobAnalysis(id=2, job_id=2, score=70, classification="Aplicar"),
        3: JobAnalysis(id=3, job_id=3, score=40, classification="Ignorar"),
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=60,
        selected_classifications=["Aplicar"],
    )

    assert [job.id for job in filtered_jobs] == [1, 2]


def test_filter_dashboard_jobs_includes_archived_jobs_when_selected() -> None:
    jobs = [
        _job(1, application_status="archived"),
        _job(2, application_status="not_applied"),
    ]
    analyses = {
        2: JobAnalysis(id=2, job_id=2, score=80, classification="Aplicar"),
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=90,
        selected_classifications=["Arquivadas"],
    )

    assert [job.id for job in filtered_jobs] == [1]


def test_build_dashboard_summary_row_keeps_table_compact() -> None:
    analysis = JobAnalysis(id=1, job_id=1, score=90, classification="Aplicar")

    row = build_dashboard_summary_row(_job(1), analysis)

    assert row == {
        "Score": 90,
        "Classificacao": "Aplicar",
        "Cargo": "Job 1",
        "Empresa": "",
        "Vaga": "",
        "Importada": "Sem data",
        "Publicada": "Sem data",
        "Localizacao": "",
        "Status": "Nova",
        "ID": 1,
    }


def test_build_dashboard_summary_row_uses_description_url_when_job_url_is_missing() -> None:
    row = build_dashboard_summary_row(
        _job(
            1,
            description="Candidate-se em https://example.com/jobs/frontend.",
        ),
        None,
    )

    assert row["Vaga"] == "https://example.com/jobs/frontend"


def test_matches_imported_date_filter_uses_job_created_at() -> None:
    job = _job(1, created_at="2026-06-12 09:30:00")

    assert matches_imported_date_filter(job, None) is True
    assert matches_imported_date_filter(job, date(2026, 6, 12)) is True
    assert matches_imported_date_filter(job, date(2026, 6, 13)) is False


def test_dashboard_candidate_excludes_applied_jobs() -> None:
    pending_job = _job(1, application_status="not_applied")
    applied_job = _job(2, application_status="applied")
    archived_job = _job(3, application_status="archived")
    not_tracking_job = _job(4, application_status="not_tracking")

    assert is_dashboard_candidate(pending_job, ["new"], None) is True
    assert is_dashboard_candidate(applied_job, ["new"], None) is False
    assert is_dashboard_candidate(archived_job, ["new"], None) is False
    assert is_dashboard_candidate(
        archived_job,
        ["new"],
        None,
        include_archived=True,
    ) is True
    assert is_dashboard_candidate(not_tracking_job, ["new"], None) is False


def test_list_recent_dashboard_jobs_falls_back_when_repository_is_stale() -> None:
    class StaleRepository:
        def list_recent(self, limit: int) -> list[Job]:
            assert limit == 100
            return [
                _job(1, application_status="not_applied"),
                _job(2, application_status="applied"),
                _job(3, application_status="archived"),
                _job(4, application_status="not_tracking"),
            ]

    jobs = list_recent_dashboard_jobs(StaleRepository(), limit=100)

    assert [job.id for job in jobs] == [1]


def test_list_recent_dashboard_jobs_can_include_archived_jobs() -> None:
    class Repository:
        def list_recent(self, limit: int) -> list[Job]:
            assert limit == 100
            return [
                _job(1, application_status="not_applied"),
                _job(2, application_status="applied"),
                _job(3, application_status="archived"),
                _job(4, application_status="not_tracking"),
            ]

    jobs = list_recent_dashboard_jobs(Repository(), limit=100, include_archived=True)

    assert [job.id for job in jobs] == [1, 3]


def _job(
    job_id: int,
    posted_at: str | None = None,
    created_at: str | None = None,
    application_status: str = "not_applied",
    description: str | None = None,
) -> Job:
    return Job(
        id=job_id,
        source_id=1,
        email_message_id=None,
        title=f"Job {job_id}",
        posted_at=posted_at,
        created_at=created_at,
        application_status=application_status,
        description=description,
        content_hash=f"hash-{job_id}",
    )
