from __future__ import annotations

from core.models import EmailMessage, JobSource

from services.parsers.generic_parser import GenericEmailParser
from services.parsers.indeed_parser import IndeedEmailParser
from services.parsers.linkedin_parser import LinkedInEmailParser


def select_email_parser(
    message: EmailMessage,
    source: JobSource | None = None,
) -> GenericEmailParser:
    parser_key = message.detected_provider or (source.parser_type if source else "")
    parser_key = parser_key.lower()

    if parser_key == "linkedin":
        return LinkedInEmailParser()
    if parser_key == "indeed":
        return IndeedEmailParser()

    return GenericEmailParser()
