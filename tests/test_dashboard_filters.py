from app.streamlit_app import filter_dashboard_jobs
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


def test_filter_dashboard_jobs_applies_score_and_classification() -> None:
    jobs = [_job(1), _job(2), _job(3)]
    analyses = {
        1: JobAnalysis(id=1, job_id=1, score=90, classification="Aplicar"),
        2: JobAnalysis(id=2, job_id=2, score=70, classification="Avaliar"),
        3: JobAnalysis(id=3, job_id=3, score=40, classification="Ignorar"),
    }

    filtered_jobs = filter_dashboard_jobs(
        jobs,
        analyses,
        minimum_score=60,
        selected_classifications=["Aplicar"],
    )

    assert [job.id for job in filtered_jobs] == [1]


def _job(job_id: int) -> Job:
    return Job(
        id=job_id,
        source_id=1,
        email_message_id=None,
        title=f"Job {job_id}",
        content_hash=f"hash-{job_id}",
    )
