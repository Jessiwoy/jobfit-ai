from pathlib import Path

import pytest
from services.gmail_service import (
    GMAIL_READONLY_SCOPES,
    GmailCredentialsMissingError,
    GmailLabel,
    GmailService,
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
