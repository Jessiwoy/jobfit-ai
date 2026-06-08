from core.models import EmailMessage
from services.email_parser import GenericEmailParser


def test_generic_parser_creates_job_from_email_subject_and_body() -> None:
    message = EmailMessage(
        id=10,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
        subject="Frontend Developer at Acme",
        received_at="2026-06-01T10:00:00-03:00",
        raw_text=(
            "Location: Remote Brazil\n"
            "We are hiring a React developer.\n"
            "Apply at https://example.com/jobs/frontend"
        ),
        detected_provider="linkedin",
    )

    jobs = GenericEmailParser().parse(message)

    assert len(jobs) == 1
    assert jobs[0].title == "Frontend Developer at Acme"
    assert jobs[0].company == "Acme"
    assert jobs[0].location == "Remote Brazil"
    assert jobs[0].work_mode == "remote"
    assert jobs[0].job_url == "https://example.com/jobs/frontend"
    assert jobs[0].provider == "linkedin"
    assert jobs[0].content_hash


def test_generic_parser_returns_no_jobs_without_title() -> None:
    message = EmailMessage(
        id=10,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
    )

    assert GenericEmailParser().parse(message) == []
