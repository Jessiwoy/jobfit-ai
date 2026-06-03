from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GMAIL_READONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailCredentialsMissingError(FileNotFoundError):
    pass


@dataclass(frozen=True)
class GmailLabel:
    id: str
    name: str


@dataclass(frozen=True)
class LabelValidationResult:
    label_name: str
    exists: bool
    label_id: str | None = None


class GmailService:
    def __init__(
        self,
        *,
        credentials_path: Path = GMAIL_CREDENTIALS_PATH,
        token_path: Path = GMAIL_TOKEN_PATH,
    ) -> None:
        self._credentials_path = credentials_path
        self._token_path = token_path

    def build_client(self) -> Any:
        credentials = self._load_credentials()
        return build("gmail", "v1", credentials=credentials)

    def list_labels(self) -> list[GmailLabel]:
        client = self.build_client()
        response = client.users().labels().list(userId="me").execute()
        labels = response.get("labels", [])

        return [
            GmailLabel(id=str(label["id"]), name=str(label["name"]))
            for label in labels
            if label.get("id") and label.get("name")
        ]

    def validate_labels(self, label_names: list[str]) -> list[LabelValidationResult]:
        labels_by_name = {label.name: label for label in self.list_labels()}

        return [
            LabelValidationResult(
                label_name=label_name,
                exists=label_name in labels_by_name,
                label_id=labels_by_name[label_name].id if label_name in labels_by_name else None,
            )
            for label_name in label_names
        ]

    def _load_credentials(self) -> Credentials:
        credentials = self._load_token()

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_token(credentials)
            return credentials

        if not self._credentials_path.exists():
            raise GmailCredentialsMissingError(
                f"Arquivo de credenciais nao encontrado: {self._credentials_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self._credentials_path),
            GMAIL_READONLY_SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        self._save_token(credentials)
        return credentials

    def _load_token(self) -> Credentials | None:
        if not self._token_path.exists():
            return None

        return Credentials.from_authorized_user_file(
            str(self._token_path),
            GMAIL_READONLY_SCOPES,
        )

    def _save_token(self, credentials: Credentials) -> None:
        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        self._token_path.write_text(credentials.to_json(), encoding="utf-8")

