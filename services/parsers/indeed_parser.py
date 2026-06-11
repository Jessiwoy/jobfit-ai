from __future__ import annotations

import re

from core.models import EmailMessage, Job

from services.parsers.generic_parser import GenericEmailParser, _clean_title, build_job_from_email

INDEED_JOB_PATTERN = re.compile(
    r"""
    (?P<title>[^\n]{3,180})\n
    (?P<company_location>[^\n]{2,120}\s+-\s+[^\n]{2,80})\n
    (?P<description>.*?)
    (?:h[aá]\s+\d+\s+dias?|rec[eé]m\s+publicada|publicada\s+h[aá]\s+\d+\s+dias?)\n
    (?P<url>https?://br\.indeed\.com/rc/clk/[^\s]+)
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)


class IndeedEmailParser(GenericEmailParser):
    provider_name = "indeed"

    def parse(self, message: EmailMessage) -> list[Job]:
        jobs = [
            build_job_from_email(
                message,
                title=match.group("title"),
                company=_split_company_location(match.group("company_location"))[0],
                location=_split_company_location(match.group("company_location"))[1],
                job_url=match.group("url"),
                description=_build_description(match),
                provider=self.provider_name,
                source_job_id_suffix=f"indeed-{index}",
            )
            for index, match in enumerate(INDEED_JOB_PATTERN.finditer(message.raw_text or ""), 1)
        ]

        return jobs or super().parse(message)

    def _extract_title(self, message: EmailMessage, text: str) -> str | None:
        subject = (message.subject or "").strip()
        if subject:
            subject = re.sub(r"^indeed\s+job\s+alert[:\s-]+", "", subject, flags=re.I)
            subject = re.sub(r"^alerta\s+do\s+indeed[:\s-]+", "", subject, flags=re.I)
            return _clean_title(subject)

        return super()._extract_title(message, text)


def _split_company_location(value: str) -> tuple[str, str | None]:
    if " - " not in value:
        return value, None

    company, location = value.split(" - ", 1)
    return company, location


def _build_description(match: re.Match[str]) -> str:
    return "\n".join(
        item.strip()
        for item in [
            match.group("title"),
            match.group("company_location"),
            match.group("description"),
            match.group("url"),
        ]
        if item and item.strip()
    )[:4000]
