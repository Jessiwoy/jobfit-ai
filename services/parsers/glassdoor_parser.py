from __future__ import annotations

import re
import unicodedata

from core.models import EmailMessage, Job

from services.parsers.generic_parser import (
    URL_PATTERN,
    GenericEmailParser,
    build_job_from_email,
    extract_relative_posted_at,
)

RATING_PATTERN = re.compile(r"^\d+(?:[.,]\d+)?\s*★$")
JOB_TITLE_KEYWORDS = (
    "analista",
    "automacao",
    "automation",
    "backend",
    "desenvolvedor",
    "developer",
    "engenharia",
    "engineer",
    "frontend",
    "front-end",
    "full stack",
    "fullstack",
    "programador",
    "qa",
    "react",
    "software",
    "trainee",
)
METADATA_PREFIXES = (
    "alerta de vaga",
    "candidate-se",
    "confira estes",
    "criar",
    "procurando algo",
    "quer ver",
    "seus anuncios",
    "seus anúncios",
    "vagas semelhantes",
    "ver mais",
    "voce recebera",
    "você receberá",
)
STOP_PREFIXES = (
    "crie alertas",
    "procurando algo",
    "quer ver",
    "vagas semelhantes",
    "voce pode editar",
    "você pode editar",
)
METADATA_VALUES = {
    "brasil",
    "candidatura rapida",
    "candidatura rápida",
    "estimativa da empresa",
    "trabalho remoto",
}


class GlassdoorEmailParser(GenericEmailParser):
    provider_name = "glassdoor"

    def parse(self, message: EmailMessage) -> list[Job]:
        lines = _job_listing_lines(_clean_lines(message.raw_text or ""))
        job_urls = _extract_job_urls(message.raw_text or "")
        jobs = []

        for index, line_index in enumerate(_job_title_indexes(lines), 1):
            company = _previous_company(lines, line_index)
            location = _next_location(lines, line_index)
            if not company:
                continue

            description = _build_description(
                title=lines[line_index],
                company=company,
                location=location,
                posted_text=_next_posted_text(lines, line_index),
            )
            jobs.append(
                build_job_from_email(
                    message,
                    title=lines[line_index],
                    company=company,
                    location=location,
                    job_url=job_urls[index - 1] if index <= len(job_urls) else None,
                    description=description,
                    provider=self.provider_name,
                    source_job_id_suffix=f"glassdoor-{index}",
                    posted_at=extract_relative_posted_at(
                        _next_posted_text(lines, line_index) or "",
                        message.received_at,
                    ),
                )
            )

        return jobs or super().parse(message)


def _clean_lines(text: str) -> list[str]:
    cleaned_text = (
        text.replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\u200e", "")
        .replace("\u200f", "")
        .replace("\ufeff", "")
        .replace("\xa0", " ")
    )
    return [
        re.sub(r"\s+", " ", line).strip()
        for line in cleaned_text.splitlines()
        if re.sub(r"\s+", " ", line).strip()
    ]


def _job_title_indexes(lines: list[str]) -> list[int]:
    return [
        index
        for index, line in enumerate(lines)
        if _is_job_title(line) and _previous_company(lines, index)
    ]


def _is_job_title(value: str) -> bool:
    normalized = _normalize(value)
    if len(normalized) < 3 or normalized in METADATA_VALUES:
        return False

    if normalized.endswith("dia(s)") or normalized.startswith(METADATA_PREFIXES):
        return False

    return any(keyword in normalized for keyword in JOB_TITLE_KEYWORDS)


def _previous_company(lines: list[str], title_index: int) -> str | None:
    index = title_index - 1
    while index >= 0 and RATING_PATTERN.match(lines[index]):
        index -= 1

    if index < 0 or not _is_company(lines[index]):
        return None

    return lines[index]


def _next_location(lines: list[str], title_index: int) -> str | None:
    if title_index + 1 >= len(lines):
        return None

    value = lines[title_index + 1]
    normalized = _normalize(value)
    if normalized.startswith("r$") or normalized.startswith("candidatura"):
        return None

    return value


def _next_posted_text(lines: list[str], title_index: int) -> str | None:
    for value in lines[title_index + 1 : title_index + 5]:
        if re.search(r"\d+\s+dia\(s\)", _normalize(value)):
            return value

    return None


def _is_company(value: str) -> bool:
    normalized = _normalize(value)
    if normalized in METADATA_VALUES or normalized.startswith(METADATA_PREFIXES):
        return False

    return not (normalized.endswith("dia(s)") or normalized.startswith("r$"))


def _job_listing_lines(lines: list[str]) -> list[str]:
    start = 0
    for index, line in enumerate(lines):
        normalized = _normalize(line)
        if normalized.startswith("seus anuncios") or normalized.startswith("seus anúncios"):
            start = index + 1
            break

    sliced = lines[start:]
    for index, line in enumerate(sliced):
        if _normalize(line).startswith(STOP_PREFIXES):
            return sliced[:index]

    return sliced


def _build_description(
    *,
    title: str,
    company: str,
    location: str | None,
    posted_text: str | None,
) -> str:
    return "\n".join(item for item in [title, company, location, posted_text] if item)[:4000]


def _extract_job_urls(text: str) -> list[str]:
    urls = [match.group(0).rstrip(".,") for match in URL_PATTERN.finditer(text)]
    glassdoor_urls = [
        url
        for url in urls
        if "glassdoor." in url.lower()
        and not any(
            ignored in url.lower()
            for ignored in ("/profile/", "/about/", "/member/", "unsubscribe")
        )
    ]
    return glassdoor_urls or urls


def _normalize(value: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()
