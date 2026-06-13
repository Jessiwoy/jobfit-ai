from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta

from core.models import EmailMessage, Job

URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)
COMPANY_PATTERNS = [
    re.compile(r"\bat\s+([A-Z][A-Za-z0-9&.,' -]{2,80})"),
    re.compile(r"\bna\s+([A-Z][A-Za-z0-9&.,' -]{2,80})"),
    re.compile(r"\bempresa[:\s]+([^\n\r]{2,80})", re.IGNORECASE),
    re.compile(r"\bcompany[:\s]+([^\n\r]{2,80})", re.IGNORECASE),
]
LOCATION_PATTERN = re.compile(
    r"\b(localizacao|localizacao|location)[:\s]+([^\n\r]{2,80})",
    re.IGNORECASE,
)
WORK_MODE_TERMS = {
    "remote": "remote",
    "remoto": "remote",
    "hybrid": "hybrid",
    "hibrido": "hybrid",
    "hibrida": "hybrid",
    "presencial": "onsite",
    "onsite": "onsite",
}
SENIORITY_TERMS = {
    "junior": "junior",
    "pleno": "mid-level",
    "mid-level": "mid-level",
    "senior": "senior",
    "lead": "lead",
}


class GenericEmailParser:
    provider_name: str | None = None

    def parse(self, message: EmailMessage) -> list[Job]:
        text = _normalized_text(message)
        title = self._extract_title(message, text)
        if not title:
            return []

        return [
            build_job_from_email(
                message,
                title=title,
                company=_extract_company(message, text),
                location=_extract_location(text),
                job_url=_extract_first_url(text),
                description=text[:4000] if text else None,
                provider=self.provider_name,
            )
        ]

    def _extract_title(self, message: EmailMessage, text: str) -> str | None:
        subject = (message.subject or "").strip()
        if subject:
            return _clean_title(subject)

        for line in text.splitlines():
            cleaned = _clean_title(line)
            if len(cleaned) >= 3:
                return cleaned

        return None


def _normalized_text(message: EmailMessage) -> str:
    return "\n".join(
        part.strip()
        for part in [message.subject or "", message.raw_text or ""]
        if part and part.strip()
    )


def build_job_from_email(
    message: EmailMessage,
    *,
    title: str,
    company: str | None,
    location: str | None,
    job_url: str | None,
    description: str | None,
    provider: str | None,
    source_job_id_suffix: str | None = None,
    posted_at: str | None = None,
) -> Job:
    source_job_id = message.gmail_message_id
    if source_job_id_suffix:
        source_job_id = f"{source_job_id}:{source_job_id_suffix}"

    return Job(
        id=None,
        source_id=message.source_id,
        email_message_id=message.id,
        title=_clean_title(title),
        company=_clean_field(company) if company else None,
        location=_clean_field(location) if location else None,
        work_mode=_extract_term(description or "", WORK_MODE_TERMS),
        seniority=_extract_term(" ".join([title, description or ""]), SENIORITY_TERMS),
        job_url=job_url,
        description=description,
        posted_at=posted_at,
        source_job_id=source_job_id,
        content_hash=_content_hash(
            source_id=message.source_id,
            title=title,
            company=company,
            job_url=job_url,
            description=description,
        ),
        provider=provider or message.detected_provider,
    )


def extract_relative_posted_at(text: str, reference_value: str | None) -> str | None:
    reference_date = _parse_reference_date(reference_value)
    if reference_date is None:
        return None

    normalized = _normalize_date_text(text)
    if re.search(r"\b(rec[eé]m publicada|rec[eé]m publicado|hoje)\b", normalized):
        return reference_date.isoformat()

    match = re.search(r"\b(?:h[aá]\s+)?(\d+)\s+dia(?:s|\(s\))?\b", normalized)
    if not match:
        return None

    return (reference_date - timedelta(days=int(match.group(1)))).isoformat()


def _clean_title(value: str) -> str:
    title = re.sub(r"\s+", " ", value).strip(" -|:")
    title = re.sub(r"^(nova vaga|new job|job alert|alerta de vaga)[:\s-]+", "", title, flags=re.I)
    return title[:180]


def _extract_company(message: EmailMessage, text: str) -> str | None:
    subject = message.subject or ""
    for pattern in COMPANY_PATTERNS:
        match = pattern.search(subject) or pattern.search(text)
        if match:
            return _clean_field(match.group(1))

    return None


def _extract_location(text: str) -> str | None:
    match = LOCATION_PATTERN.search(text)
    if not match:
        return None

    return _clean_field(match.group(2))


def _extract_first_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    if not match:
        return None

    return match.group(0).rstrip(".,")


def _extract_term(text: str, terms: dict[str, str]) -> str | None:
    normalized = text.lower()
    for term, value in terms.items():
        if term in normalized:
            return value

    return None


def _clean_field(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -|:.")[:120]


def _parse_reference_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _normalize_date_text(value: str) -> str:
    return value.lower().replace("á", "a").replace("é", "e")


def _content_hash(
    *,
    source_id: int,
    title: str,
    company: str | None,
    job_url: str | None,
    description: str | None,
) -> str:
    payload = "|".join(
        [
            str(source_id),
            title.lower().strip(),
            (company or "").lower().strip(),
            (job_url or "").lower().strip(),
            (description or "")[:500].lower().strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
