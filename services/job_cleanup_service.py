from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from core.models import Job, Preferences
from repositories.jobs_repository import JobsRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.user_repository import UserRepository


@dataclass(frozen=True)
class JobCleanupSummary:
    reviewed_jobs: int
    duplicate_jobs: int
    old_jobs: int
    incompatible_jobs: int


class JobCleanupService:
    def __init__(self, database_path: Path) -> None:
        self._jobs_repository = JobsRepository(database_path)
        self._user_repository = UserRepository(database_path)
        self._preferences_repository = PreferencesRepository(database_path)

    def cleanup_jobs(
        self,
        *,
        max_age_days: int = 45,
        today: date | None = None,
    ) -> JobCleanupSummary:
        jobs = self._jobs_repository.list_all()
        user = self._user_repository.get_or_create_default_user()
        preferences = self._preferences_repository.get_by_user_id(user.id)
        reference_date = today or datetime.now(UTC).date()

        duplicate_ids = self._find_duplicate_ids(jobs)
        old_ids = self._find_old_ids(jobs, duplicate_ids, max_age_days, reference_date)
        incompatible_ids = self._find_incompatible_ids(
            jobs,
            duplicate_ids | old_ids,
            preferences,
        )

        self._mark_jobs(duplicate_ids, "duplicate")
        self._mark_jobs(old_ids, "old")
        self._mark_jobs(incompatible_ids, "incompatible")

        return JobCleanupSummary(
            reviewed_jobs=len(jobs),
            duplicate_jobs=len(duplicate_ids),
            old_jobs=len(old_ids),
            incompatible_jobs=len(incompatible_ids),
        )

    def _find_duplicate_ids(self, jobs: list[Job]) -> set[int]:
        seen_keys: set[str] = set()
        duplicate_ids: set[int] = set()

        for job in jobs:
            if job.id is None or job.status != "new":
                continue

            keys = _deduplication_keys(job)
            if any(key in seen_keys for key in keys):
                duplicate_ids.add(job.id)
                continue

            seen_keys.update(keys)

        return duplicate_ids

    def _find_old_ids(
        self,
        jobs: list[Job],
        ignored_ids: set[int],
        max_age_days: int,
        today: date,
    ) -> set[int]:
        cutoff = today - timedelta(days=max_age_days)
        old_ids: set[int] = set()

        for job in jobs:
            if job.id is None or job.id in ignored_ids or job.status != "new":
                continue

            posted_date = _parse_date(job.posted_at)
            if posted_date is not None and posted_date < cutoff:
                old_ids.add(job.id)

        return old_ids

    def _find_incompatible_ids(
        self,
        jobs: list[Job],
        ignored_ids: set[int],
        preferences: Preferences,
    ) -> set[int]:
        incompatible_ids: set[int] = set()

        for job in jobs:
            if job.id is None or job.id in ignored_ids or job.status != "new":
                continue

            if _is_incompatible(job, preferences):
                incompatible_ids.add(job.id)

        return incompatible_ids

    def _mark_jobs(self, job_ids: set[int], status: str) -> None:
        for job_id in job_ids:
            self._jobs_repository.update_status(job_id, status)


def _deduplication_keys(job: Job) -> list[str]:
    keys = []
    normalized_url = _normalize_url(job.job_url)
    if normalized_url:
        keys.append(f"url:{normalized_url}")

    title = _normalize_text(job.title)
    company = _normalize_text(job.company)
    location = _normalize_text(job.location)
    if title and company:
        keys.append(f"identity:{title}|{company}|{location}")

    return keys


def _normalize_url(value: str | None) -> str | None:
    if not value:
        return None

    parsed = urlsplit(value.strip())
    if not parsed.netloc:
        return _normalize_text(value)

    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        pass

    try:
        return date.fromisoformat(normalized[:10])
    except ValueError:
        return None


def _is_incompatible(job: Job, preferences: Preferences) -> bool:
    searchable_text = _normalize_text(
        " ".join(
            value or ""
            for value in [
                job.title,
                job.company,
                job.location,
                job.work_mode,
                job.seniority,
                job.description,
            ]
        )
    )

    if _contains_any(searchable_text, preferences.undesired_terms):
        return True

    if job.work_mode and preferences.work_modes:
        return not _matches_any(job.work_mode, preferences.work_modes)

    if job.location and preferences.locations:
        return not _matches_any(job.location, preferences.locations)

    if job.seniority and preferences.seniority:
        return not _matches_any(job.seniority, preferences.seniority)

    return False


def _contains_any(value: str, terms: list[str]) -> bool:
    return any(_normalize_text(term) in value for term in terms if term.strip())


def _matches_any(value: str, accepted_values: list[str]) -> bool:
    normalized_value = _normalize_text(value)
    return any(
        normalized_value in accepted_value or accepted_value in normalized_value
        for accepted_value in [_normalize_text(item) for item in accepted_values if item.strip()]
    )


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(r"\s+", " ", value).strip().lower()
