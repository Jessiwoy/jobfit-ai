from pathlib import Path

import pytest
from core.models import JobSource
from services.gmail_service import (
    GMAIL_READONLY_SCOPES,
    GmailCredentialsMissingError,
    GmailLabel,
    GmailService,
    detect_provider,
)


class FakeGmailService(GmailService):
    def __init__(self, labels: list[GmailLabel]) -> None:
        self._labels = labels

    def list_labels(self) -> list[GmailLabel]:
        return self._labels


def test_gmail_scope_is_readonly() -> None:
    assert GMAIL_READONLY_SCOPES == ["https://www.googleapis.com/auth/gmail.readonly"]


def test_validate_labels_matches_by_exact_name() -> None:
    service = FakeGmailService(
        [
            GmailLabel(id="Label_1", name="Job Alerts"),
        ]
    )

    results = service.validate_labels(["Job Alerts", "Missing Jobs"])

    assert results[0].exists is True
    assert results[0].label_id == "Label_1"
    assert results[1].exists is False
    assert results[1].label_id is None


def test_missing_credentials_raise_clear_error(tmp_path: Path) -> None:
    service = GmailService(
        credentials_path=tmp_path / "credentials.json",
        token_path=tmp_path / "token.json",
    )

    with pytest.raises(GmailCredentialsMissingError):
        service.build_client()


def test_detect_provider_from_content() -> None:
    assert detect_provider("New job from LinkedIn") == "linkedin"
    assert detect_provider("Veja a vaga em indeed.com") == "indeed"
    assert detect_provider("Unknown source") is None


def test_parse_message_payload_extracts_metadata_and_body() -> None:
    source = JobSource(
        id=1,
        name="Job Alerts",
        gmail_label_name="Job Alerts",
        source_type="gmail_label",
        parser_type="generic",
        enabled=True,
    )
    service = GmailService()

    message = service._parse_message_payload(  # noqa: SLF001
        source,
        {
            "id": "msg-1",
            "threadId": "thread-1",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Frontend Developer at LinkedIn"},
                    {"name": "From", "value": "jobs@example.com"},
                    {"name": "Date", "value": "Mon, 01 Jun 2026 10:00:00 -0300"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "VGVzdGUgZGUgdmFnYQ=="},
                    }
                ],
            },
        },
    )

    assert message.gmail_message_id == "msg-1"
    assert message.gmail_thread_id == "thread-1"
    assert message.subject == "Frontend Developer at LinkedIn"
    assert message.sender == "jobs@example.com"
    assert message.raw_text == "Teste de vaga"
    assert message.detected_provider == "linkedin"
