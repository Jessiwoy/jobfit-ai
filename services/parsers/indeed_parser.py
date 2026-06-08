from __future__ import annotations

import re

from core.models import EmailMessage

from services.parsers.generic_parser import GenericEmailParser, _clean_title


class IndeedEmailParser(GenericEmailParser):
    provider_name = "indeed"

    def _extract_title(self, message: EmailMessage, text: str) -> str | None:
        subject = (message.subject or "").strip()
        if subject:
            subject = re.sub(r"^indeed\s+job\s+alert[:\s-]+", "", subject, flags=re.I)
            subject = re.sub(r"^alerta\s+do\s+indeed[:\s-]+", "", subject, flags=re.I)
            return _clean_title(subject)

        return super()._extract_title(message, text)
