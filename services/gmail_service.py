from __future__ import annotations

import base64
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from core.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from core.models import EmailMessage, JobSource
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

GMAIL_READONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailCredentialsMissingError(FileNotFoundError):
    pass


class GmailAuthenticationError(RuntimeError):
    pass


class GmailLabelNotFoundError(ValueError):
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

    def fetch_messages_for_source(
        self,
        source: JobSource,
        *,
        max_results: int = 25,
        existing_message_ids: set[str] | None = None,
    ) -> list[EmailMessage]:
        label = self._get_label_by_name(source.gmail_label_name)
        client = self.build_client()
        existing_ids = existing_message_ids or set()
        message_refs = self._list_message_refs(client, label.id, max_results=max_results)
        messages = []

        for message_ref in message_refs:
            message_id = str(message_ref.get("id") or "")
            if not message_id or message_id in existing_ids:
                continue

            payload = (
                client.users().messages().get(userId="me", id=message_id, format="full").execute()
            )
            messages.append(self._parse_message_payload(source, payload))

        return messages

    def _get_label_by_name(self, label_name: str) -> GmailLabel:
        for label in self.list_labels():
            if label.name == label_name:
                return label

        raise GmailLabelNotFoundError(f"Label nao encontrada no Gmail: {label_name}")

    def _list_message_refs(
        self,
        client: Any,
        label_id: str,
        *,
        max_results: int,
    ) -> list[dict[str, Any]]:
        response = (
            client.users()
            .messages()
            .list(
                userId="me",
                labelIds=[label_id],
                maxResults=max_results,
            )
            .execute()
        )
        return list(response.get("messages", []))

    def _parse_message_payload(self, source: JobSource, payload: dict[str, Any]) -> EmailMessage:
        headers = _headers_by_name(payload.get("payload", {}).get("headers", []))
        raw_text, raw_html = _extract_message_bodies(payload.get("payload", {}))
        sender = headers.get("from")
        subject = headers.get("subject")
        received_at = _parse_received_at(headers.get("date"))
        detected_provider = detect_provider(
            " ".join(
                [
                    sender or "",
                    subject or "",
                    raw_text or "",
                    raw_html or "",
                ]
            )
        )

        return EmailMessage(
            id=None,
            source_id=source.id,
            gmail_message_id=str(payload["id"]),
            gmail_thread_id=str(payload.get("threadId") or "") or None,
            gmail_label_name=source.gmail_label_name,
            subject=subject,
            sender=sender,
            received_at=received_at,
            raw_text=raw_text,
            raw_html=raw_html,
            detected_provider=detected_provider,
        )

    def _load_credentials(self) -> Credentials:
        credentials = self._load_token()

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self._save_token(credentials)
                return credentials
            except RefreshError as error:
                self._raise_reauthorization_required(error)
            except Exception as error:
                if _is_invalid_grant_error(error):
                    self._raise_reauthorization_required(error)
                raise

        if not self._credentials_path.exists():
            raise GmailCredentialsMissingError(
                f"Arquivo de credenciais nao encontrado: {self._credentials_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self._credentials_path),
            GMAIL_READONLY_SCOPES,
        )
        try:
            credentials = flow.run_local_server(port=0)
        except Exception as error:
            if _is_invalid_grant_error(error):
                self._raise_reauthorization_required(error)
            raise
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

    def _delete_token(self) -> None:
        if self._token_path.exists():
            self._token_path.unlink()

    def _raise_reauthorization_required(self, error: Exception) -> None:
        self._delete_token()
        raise GmailAuthenticationError(
            "A autorizacao do Gmail expirou ou foi revogada. "
            "O token local antigo foi removido. Clique em buscar e-mails novamente "
            "e autorize a conta no navegador."
        ) from error


def _is_invalid_grant_error(error: Exception) -> bool:
    return "invalid_grant" in str(error).lower()


def detect_provider(content: str) -> str | None:
    normalized = content.lower()

    if "linkedin" in normalized or "linkedin.com" in normalized:
        return "linkedin"
    if "indeed" in normalized or "indeed.com" in normalized:
        return "indeed"
    if "glassdoor" in normalized or "glassdoor.com" in normalized:
        return "glassdoor"
    if "gupy" in normalized or "gupy.io" in normalized:
        return "gupy"

    return None


def _headers_by_name(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(header["name"]).lower(): str(header["value"])
        for header in headers
        if header.get("name") and header.get("value")
    }


def _parse_received_at(value: str | None) -> str | None:
    if not value:
        return None

    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError, IndexError):
        return value


def _extract_message_bodies(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    text_parts: list[str] = []
    html_parts: list[str] = []

    for part in _iter_payload_parts(payload):
        mime_type = str(part.get("mimeType") or "")
        data = part.get("body", {}).get("data")
        if not data:
            continue

        decoded = _decode_gmail_data(str(data))
        if mime_type == "text/plain":
            text_parts.append(decoded)
        elif mime_type == "text/html":
            html_parts.append(decoded)

    raw_html = "\n\n".join(html_parts).strip() or None
    raw_text = "\n\n".join(text_parts).strip() or None

    if not raw_text and raw_html:
        raw_text = BeautifulSoup(raw_html, "html.parser").get_text("\n", strip=True)

    return raw_text, raw_html


def _iter_payload_parts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    parts = payload.get("parts")
    if not parts:
        return [payload]

    flattened = []
    for part in parts:
        flattened.extend(_iter_payload_parts(part))

    return flattened


def _decode_gmail_data(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8", errors="replace")
