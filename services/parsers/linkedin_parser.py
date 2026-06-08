from __future__ import annotations

import re

from core.models import EmailMessage

from services.parsers.generic_parser import GenericEmailParser, _clean_title


class LinkedInEmailParser(GenericEmailParser):
    provider_name = "linkedin"

    def _extract_title(self, message: EmailMessage, text: str) -> str | None:
        subject = (message.subject or "").strip()
        if subject:
            subject = re.sub(r"^linkedin\s+job\s+alert[:\s-]+", "", subject, flags=re.I)
            subject = re.sub(r"^vagas?\s+recomendadas?[:\s-]+", "", subject, flags=re.I)
            return _clean_title(subject)

        return super()._extract_title(message, text)
