from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    id: int
    name: str | None = None
    email: str | None = None
    current_title: str | None = None
    location: str | None = None
    summary: str | None = None


@dataclass(frozen=True)
class Preferences:
    id: int | None
    user_id: int
    desired_titles: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    work_modes: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)
    undesired_terms: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JobSource:
    id: int
    name: str
    gmail_label_name: str
    source_type: str
    parser_type: str
    enabled: bool


@dataclass(frozen=True)
class ProfileItem:
    id: int | None
    user_id: int
    item_type: str
    name: str
    level: str | None = None
    years_experience: float | None = None
    evidence: str | None = None

