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
class EmailMessage:
    id: int | None
    source_id: int
    gmail_message_id: str
    gmail_thread_id: str | None
    gmail_label_name: str
    subject: str | None = None
    sender: str | None = None
    received_at: str | None = None
    raw_text: str | None = None
    raw_html: str | None = None
    detected_provider: str | None = None
    processed_status: str = "new"
    error_message: str | None = None


@dataclass(frozen=True)
class Job:
    id: int | None
    source_id: int
    email_message_id: int | None
    title: str
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None
    seniority: str | None = None
    job_url: str | None = None
    description: str | None = None
    posted_at: str | None = None
    source_job_id: str | None = None
    content_hash: str = ""
    status: str = "new"
    provider: str | None = None
    application_status: str = "not_applied"
    applied_at: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class ProfileItem:
    id: int | None
    user_id: int
    item_type: str
    name: str
    level: str | None = None
    years_experience: float | None = None
    evidence: str | None = None


