from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from core.models import ProfileItem
from pypdf import PdfReader

TECHNOLOGY_TERMS = [
    "React",
    "React.js",
    "React Native",
    "TypeScript",
    "JavaScript",
    "Node.js",
    "Express.js",
    "APIs REST",
    "Next.js",
    "Next.js API Routes",
    "Next.js App Router",
    "HTML5",
    "CSS3",
    "TailwindCSS",
    "Vite",
    "Jest",
    "MySQL",
    "Docker",
    "AWS",
    "EC2",
    "S3",
    "CI/CD",
    "Vercel Analytics",
    "Redux",
    "JWT",
    "React Hook Form",
    "Zod",
    "EmailJS",
    "Git",
]

SKILL_TERMS = [
    "Domain-Driven Design",
    "DDD",
    "SOLID",
    "Atomic Design",
    "Design System",
    "Clean Code",
    "Arquitetura modular",
    "Componentização reutilizável",
    "Testes unitários",
    "Testes de integração",
    "Scrum",
    "Kanban",
    "Code reviews",
    "DevOps",
    "Cloud",
    "SEO",
    "LGPD",
]

PROJECT_NAMES = [
    "Programa Flexível",
    "IOOH",
    "Escutas e Travessias",
    "Property Sales",
    "Taskly",
    "Taskly + AWS",
]


@dataclass(frozen=True)
class ResumeExtraction:
    raw_text: str
    readable_text: str


@dataclass(frozen=True)
class ResumeAutofill:
    name: str | None
    email: str | None
    current_title: str | None
    location: str | None
    summary: str | None
    desired_titles: list[str]
    seniority: list[str]
    technologies: list[str]
    work_modes: list[str]
    locations: list[str]
    required_terms: list[str]
    profile_items: list[ProfileItem]


def extract_resume_pdf(pdf_bytes: bytes) -> ResumeExtraction:
    reader = PdfReader(BytesIO(pdf_bytes))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    raw_text = "\n\n".join(
        f"--- PAGE {index} ---\n{text.strip()}"
        for index, text in enumerate(page_texts, 1)
    ).strip()
    return ResumeExtraction(raw_text=raw_text, readable_text=make_pdf_text_readable(raw_text))


def make_pdf_text_readable(text: str) -> str:
    return "\n".join(_make_line_readable(line) for line in text.splitlines()).strip()


def write_profile_extracted(path: Path, extraction: ResumeExtraction) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Perfil extraido do curriculo",
                "",
                "> Arquivo local com dados sensiveis extraidos do curriculo. Nao versionar.",
                "> Texto extraido do PDF sem resumo ou reescrita manual.",
                "",
                "## Texto extraido",
                "",
                "```text",
                extraction.readable_text,
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_resume_autofill(
    *,
    user_id: int,
    readable_text: str,
) -> ResumeAutofill:
    lines = [line.strip() for line in readable_text.splitlines() if line.strip()]
    full_text = "\n".join(lines)

    technologies = [term for term in TECHNOLOGY_TERMS if _contains_term(full_text, term)]
    skills = [term for term in SKILL_TERMS if _contains_term(full_text, term)]
    project_items = _build_named_items(
        user_id=user_id,
        item_type="project",
        names=PROJECT_NAMES,
        text=full_text,
    )

    profile_items = (
        _build_term_items(
            user_id=user_id,
            item_type="technology",
            terms=technologies,
            text=full_text,
        )
        + _build_term_items(
            user_id=user_id,
            item_type="skill",
            terms=skills,
            text=full_text,
        )
        + _build_experience_items(user_id=user_id, text=full_text)
        + project_items
        + _build_education_items(user_id=user_id, text=full_text)
    )

    return ResumeAutofill(
        name=_extract_name(lines),
        email=_extract_email(full_text),
        current_title=_extract_current_title(lines),
        location=_extract_location(lines),
        summary=_extract_summary(lines),
        desired_titles=[
            "Desenvolvedora de Software",
            "Desenvolvedora Frontend",
            "Desenvolvedora React",
            "Desenvolvedora Full Stack",
            "Frontend Developer",
            "React Developer",
            "React Native Developer",
            "Full Stack Developer",
            "Software Developer",
        ],
        seniority=["Junior", "Pleno"],
        technologies=technologies,
        work_modes=[],
        locations=["Brasil", "Palhoça", "Santa Catarina"],
        required_terms=["React", "TypeScript"],
        profile_items=_deduplicate_profile_items(profile_items),
    )


def _make_line_readable(line: str) -> str:
    if not line.strip():
        return ""

    parts = re.split(r" {2,}", line.strip())
    readable_parts = []
    for part in parts:
        tokens = part.split()
        single_char_ratio = sum(1 for token in tokens if len(token) == 1) / max(len(tokens), 1)
        if len(tokens) > 1 and single_char_ratio >= 0.7:
            readable_parts.append("".join(tokens))
        else:
            readable_parts.append(part)

    return " ".join(readable_parts)


def _extract_name(lines: list[str]) -> str | None:
    for first, second in zip(lines, lines[1:], strict=False):
        if first.upper() == "JESSICA" and second.upper() == "WOYTUSKI":
            return "Jessica Woytuski"
    return None


def _extract_email(text: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    return match.group(0) if match else None


def _extract_current_title(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if line == "JESSICA" and index + 3 < len(lines):
            return _join_wrapped_title(lines, index + 3)

    for line in lines:
        if "Desenvolvedora de Software" in line or "Desenvolvedor de Software" in line:
            return line

    return None


def _join_wrapped_title(lines: list[str], start_index: int) -> str:
    title_lines = [lines[start_index]]
    for line in lines[start_index + 1 : start_index + 3]:
        if _looks_like_contact_line(line):
            break
        title_lines.append(line)

    return " ".join(title_lines)


def _looks_like_contact_line(line: str) -> bool:
    return bool(
        re.search(r"@|\(\d{2}\)|linkedin\.com|github\.com|palhoça|brasil", line, re.IGNORECASE)
    )


def _extract_location(lines: list[str]) -> str | None:
    for line in lines:
        if "Palhoça" in line and "Brasil" in line:
            return line
    return None


def _extract_summary(lines: list[str]) -> str | None:
    start = 1 if lines and lines[0].startswith("--- PAGE") else 0
    end_markers = {"Especializações:"}
    summary_lines = []
    for line in lines[start:]:
        if line in end_markers:
            break
        if line.startswith("--- PAGE"):
            continue
        summary_lines.append(line)

    return "\n".join(summary_lines).strip() or None


def _build_term_items(
    *,
    user_id: int,
    item_type: str,
    terms: list[str],
    text: str,
) -> list[ProfileItem]:
    return [
        ProfileItem(
            id=None,
            user_id=user_id,
            item_type=item_type,
            name=term,
            evidence=_evidence_for_term(text, term),
        )
        for term in terms
    ]


def _build_named_items(
    *,
    user_id: int,
    item_type: str,
    names: list[str],
    text: str,
) -> list[ProfileItem]:
    return [
        ProfileItem(
            id=None,
            user_id=user_id,
            item_type=item_type,
            name=name,
            evidence=_section_after_heading(text, name),
        )
        for name in names
        if _contains_term(text, name)
    ]


def _build_experience_items(*, user_id: int, text: str) -> list[ProfileItem]:
    experiences = []
    for company in ["Rovaris Tech - PJ", "Compass UOL - Estágio"]:
        if _contains_term(text, company):
            experiences.append(
                ProfileItem(
                    id=None,
                    user_id=user_id,
                    item_type="experience",
                    name=company,
                    evidence=_section_after_heading(text, company),
                )
            )
    return experiences


def _build_education_items(*, user_id: int, text: str) -> list[ProfileItem]:
    education_names = [
        "Universidade do Sul de Santa Catarina - UNISUL",
        "Instituto Federal de Santa Catarina - IFSC",
    ]
    return _build_named_items(
        user_id=user_id,
        item_type="education",
        names=education_names,
        text=text,
    )


def _evidence_for_term(text: str, term: str) -> str | None:
    matching_lines = [
        line.strip()
        for line in text.splitlines()
        if _contains_term(line, term)
    ]
    return "\n".join(matching_lines[:3]) or None


def _section_after_heading(text: str, heading: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _normalize(line) == _normalize(heading):
            section_lines = []
            for next_line in lines[index + 1 : index + 8]:
                if next_line.startswith("--- PAGE"):
                    continue
                section_lines.append(next_line)
            return "\n".join(section_lines).strip() or None
    return _evidence_for_term(text, heading)


def _deduplicate_profile_items(items: list[ProfileItem]) -> list[ProfileItem]:
    seen = set()
    unique_items = []
    for item in items:
        key = (item.item_type, _normalize(item.name))
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)
    return unique_items


def _contains_term(text: str, term: str) -> bool:
    return _normalize(term) in _normalize(text)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()
