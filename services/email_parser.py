from __future__ import annotations

import hashlib
import re

from core.models import EmailMessage, Job

URL_PATTERN = re.compile(r"https?://[^\s<>\")]+", re.IGNORECASE)
COMPANY_PATTERNS = [
    re.compile(r"\bat\s+([A-Z][A-Za-z0-9&.,' -]{2,80})"),
    re.compile(r"\bna\s+([A-Z][A-Za-z0-9&.,' -]{2,80})"),
    re.compile(r"\bempresa[:\s]+([^\n\r]{2,80})", re.IGNORECASE),
    re.compile(r"\bcompany[:\s]+([^\n\r]{2,80})", re.IGNORECASE),
]
LOCATION_PATTERN = re.compile(
    r"\b(localizacao|localiza[cç][aã]o|location)[:\s]+([^\n\r]{2,80})",
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
    "júnior": "junior",
    "pleno": "mid-level",
    "mid-level": "mid-level",
    "senior": "senior",
    "sênior": "senior",
    "lead": "lead",
}


class GenericEmailParser:
    def parse(self, message: EmailMessage) -> list[Job]:
        text = _normalized_text(message)
        title = _extract_title(message, text)
        if not title:
            return []

        company = _extract_company(message, text)
        job_url = _extract_first_url(text)
        description = text[:4000] if text else None

        job = Job(
            id=None,
            source_id=message.source_id,
            email_message_id=message.id,
            title=title,
            company=company,
            location=_extract_location(text),
            work_mode=_extract_term(text, WORK_MODE_TERMS),
            seniority=_extract_term(text, SENIORITY_TERMS),
            job_url=job_url,
            description=description,
            posted_at=message.received_at,
            source_job_id=message.gmail_message_id,
            content_hash=_content_hash(
                source_id=message.source_id,
                title=title,
                company=company,
                job_url=job_url,
                description=description,
            ),
            provider=message.detected_provider,
        )

        return [job]


def _normalized_text(message: EmailMessage) -> str:
    return "\n".join(
        part.strip()
        for part in [message.subject or "", message.raw_text or ""]
        if part and part.strip()
    )


def _extract_title(message: EmailMessage, text: str) -> str | None:
    subject = (message.subject or "").strip()
    if subject:
        return _clean_title(subject)

    for line in text.splitlines():
        cleaned = _clean_title(line)
        if len(cleaned) >= 3:
            return cleaned

    return None


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
