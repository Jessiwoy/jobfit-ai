from __future__ import annotations

import re

from core.models import EmailMessage, Job

from services.parsers.generic_parser import GenericEmailParser, _clean_title, build_job_from_email

LINKEDIN_JOB_URL_PATTERN = re.compile(
    r"Visualizar\s+vaga:\s*(?P<url>https?://www\.linkedin\.com/(?:comm/)?jobs/view/[^\s]+)",
    re.IGNORECASE,
)
LINKEDIN_SKIP_LINES = (
    "candidate-se",
    "esta empresa",
    "visualizar vaga",
)


class LinkedInEmailParser(GenericEmailParser):
    provider_name = "linkedin"

    def parse(self, message: EmailMessage) -> list[Job]:
        jobs = []
        text = message.raw_text or ""
        previous_end = 0

        for index, match in enumerate(LINKEDIN_JOB_URL_PATTERN.finditer(text), 1):
            block = text[previous_end : match.start()]
            previous_end = match.end()
            fields = _extract_job_fields(block)
            if fields is None:
                continue

            title, company, location = fields
            jobs.append(
                build_job_from_email(
                    message,
                    title=title,
                    company=company,
                    location=location,
                    job_url=match.group("url"),
                    description=_build_description(
                        title=title,
                        company=company,
                        location=location,
                        block=block,
                        url=match.group("url"),
                    ),
                    provider=self.provider_name,
                    source_job_id_suffix=f"linkedin-{index}",
                )
            )

        return jobs or super().parse(message)

    def _extract_title(self, message: EmailMessage, text: str) -> str | None:
        subject = (message.subject or "").strip()
        if subject:
            subject = re.sub(r"^linkedin\s+job\s+alert[:\s-]+", "", subject, flags=re.I)
            subject = re.sub(r"^vagas?\s+recomendadas?[:\s-]+", "", subject, flags=re.I)
            return _clean_title(subject)

        return super()._extract_title(message, text)


def _extract_job_fields(block: str) -> tuple[str, str, str] | None:
    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip() and not _is_linkedin_metadata(line.strip())
    ]
    lines = [
        line
        for line in lines
        if not line.lower().startswith(LINKEDIN_SKIP_LINES)
        and "ex-aluno" not in line.lower()
        and set(line) != {"-"}
    ]

    if len(lines) < 3:
        return None

    title, company, location = lines[-3:]
    if not title.strip("- |:") or not company.strip("- |:"):
        return None

    return title, company, location


def _is_linkedin_metadata(value: str) -> bool:
    normalized = value.lower()
    return normalized.startswith(
        (
            "resultados da nova pesquisa",
            "gerenciar alertas",
            "ver todas as vagas",
            "seu alerta de vaga",
        )
    )


def _build_description(
    *,
    title: str,
    company: str,
    location: str,
    block: str,
    url: str,
) -> str:
    return "\n".join(
        item.strip()
        for item in [
            title,
            company,
            location,
            block,
            url,
        ]
        if item and item.strip()
    )[:4000]
