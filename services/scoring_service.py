from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.analysis_models import JobAnalysis
from core.models import Job, Preferences, ProfileItem
from repositories.analyses_repository import AnalysesRepository
from repositories.jobs_repository import JobsRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.profile_items_repository import ProfileItemsRepository
from repositories.user_repository import UserRepository


@dataclass(frozen=True)
class ScoringSummary:
    reviewed_jobs: int
    analyzed_jobs: int
    skipped_jobs: int = 0


@dataclass(frozen=True)
class ScoringCriteriaSummary:
    desired_titles: int
    seniority: int
    technologies: int
    work_modes: int
    locations: int
    required_terms: int
    undesired_terms: int
    profile_items: int

    @property
    def can_score(self) -> bool:
        return any(
            [
                self.desired_titles,
                self.seniority,
                self.technologies,
                self.work_modes,
                self.locations,
                self.required_terms,
                self.undesired_terms,
                self.profile_items,
            ]
        )


class ScoringService:
    def __init__(self, database_path: Path) -> None:
        self._jobs_repository = JobsRepository(database_path)
        self._user_repository = UserRepository(database_path)
        self._preferences_repository = PreferencesRepository(database_path)
        self._profile_items_repository = ProfileItemsRepository(database_path)
        self._analyses_repository = AnalysesRepository(database_path)

    def score_new_jobs(self) -> ScoringSummary:
        user = self._user_repository.get_or_create_default_user()
        preferences = self._preferences_repository.get_by_user_id(user.id)
        profile_items = self._profile_items_repository.list_by_user_id(user.id)
        jobs = [job for job in self._jobs_repository.list_all() if job.id and job.status == "new"]

        if not _has_scoring_criteria(preferences, profile_items):
            return ScoringSummary(
                reviewed_jobs=len(jobs),
                analyzed_jobs=0,
                skipped_jobs=len(jobs),
            )

        for job in jobs:
            self._analyses_repository.upsert(
                build_job_analysis(job, preferences, profile_items)
            )

        return ScoringSummary(reviewed_jobs=len(jobs), analyzed_jobs=len(jobs))

    def get_criteria_summary(self) -> ScoringCriteriaSummary:
        user = self._user_repository.get_or_create_default_user()
        preferences = self._preferences_repository.get_by_user_id(user.id)
        profile_items = self._profile_items_repository.list_by_user_id(user.id)

        return ScoringCriteriaSummary(
            desired_titles=len(preferences.desired_titles),
            seniority=len(preferences.seniority),
            technologies=len(preferences.technologies),
            work_modes=len(preferences.work_modes),
            locations=len(preferences.locations),
            required_terms=len(preferences.required_terms),
            undesired_terms=len(preferences.undesired_terms),
            profile_items=len(profile_items),
        )


def build_job_analysis(
    job: Job,
    preferences: Preferences,
    profile_items: list[ProfileItem],
) -> JobAnalysis:
    if job.id is None:
        raise ValueError("Nao e possivel analisar vaga sem ID.")

    job_text = _job_text(job)
    profile_terms = _profile_terms(profile_items)
    desired_title_matches = _matched_terms(job_text, preferences.desired_titles)
    technology_matches = _matched_terms(job_text, preferences.technologies + profile_terms)
    work_mode_matches = _matched_terms(_normalize(job.work_mode), preferences.work_modes)
    location_matches = _matched_terms(_normalize(job.location), preferences.locations)
    seniority_matches = _matched_terms(_normalize(job.seniority), preferences.seniority)
    required_matches = _matched_terms(job_text, preferences.required_terms)
    undesired_matches = _matched_terms(job_text, preferences.undesired_terms)

    score = 0
    strengths = []
    gaps = []

    score += _weighted_score(desired_title_matches, preferences.desired_titles, 20)
    if desired_title_matches:
        strengths.append("Cargo alinhado com as preferências.")
    elif preferences.desired_titles:
        gaps.append("Cargo não corresponde claramente aos cargos desejados.")

    score += _weighted_score(technology_matches, preferences.technologies + profile_terms, 30)
    if technology_matches:
        strengths.append("Tecnologias ou habilidades relevantes encontradas.")
    elif preferences.technologies or profile_terms:
        gaps.append("Tecnologias desejadas não aparecem claramente na vaga.")

    score += _weighted_score(work_mode_matches, preferences.work_modes, 15)
    if work_mode_matches:
        strengths.append("Modalidade compatível.")
    elif preferences.work_modes:
        gaps.append("Modalidade não confirmada como compatível.")

    score += _weighted_score(location_matches, preferences.locations, 15)
    if location_matches:
        strengths.append("Localização compatível.")
    elif preferences.locations:
        gaps.append("Localização não confirmada como compatível.")

    score += _weighted_score(seniority_matches, preferences.seniority, 10)
    if seniority_matches:
        strengths.append("Senioridade compatível.")
    elif preferences.seniority:
        gaps.append("Senioridade não confirmada como compatível.")

    score += _weighted_score(required_matches, preferences.required_terms, 10)
    if required_matches:
        strengths.append("Termos obrigatórios encontrados.")
    elif preferences.required_terms:
        gaps.append("Termos obrigatórios não aparecem claramente.")

    if undesired_matches:
        score -= 30
        gaps.append("Termos indesejados encontrados.")

    normalized_score = max(0, min(100, round(score)))
    classification = _classification(normalized_score)
    matched_terms = _unique_terms(
        desired_title_matches
        + technology_matches
        + work_mode_matches
        + location_matches
        + seniority_matches
        + required_matches
    )
    missing_terms = _missing_terms(preferences, matched_terms)

    return JobAnalysis(
        id=None,
        job_id=job.id,
        score=normalized_score,
        classification=classification,
        strengths=strengths,
        gaps=gaps,
        recommendation_reason=_recommendation_reason(normalized_score, strengths, gaps),
        matched_terms=matched_terms,
        missing_terms=missing_terms,
        undesired_terms_found=undesired_matches,
    )


def _job_text(job: Job) -> str:
    return _normalize(
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


def _profile_terms(profile_items: list[ProfileItem]) -> list[str]:
    return [
        item.name
        for item in profile_items
        if item.item_type in {"technology", "skill"} and item.name.strip()
    ]


def _has_scoring_criteria(
    preferences: Preferences,
    profile_items: list[ProfileItem],
) -> bool:
    return any(
        [
            preferences.desired_titles,
            preferences.seniority,
            preferences.technologies,
            preferences.work_modes,
            preferences.locations,
            preferences.required_terms,
            preferences.undesired_terms,
            _profile_terms(profile_items),
        ]
    )


def _weighted_score(matches: list[str], expected_terms: list[str], weight: int) -> float:
    terms = [term for term in expected_terms if term.strip()]
    if not terms:
        return 0

    return weight * min(1, len(matches) / len(terms))


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    normalized_terms = [_normalize(term) for term in terms if term.strip()]
    return _unique_terms([term for term in normalized_terms if term and term in text])


def _missing_terms(preferences: Preferences, matched_terms: list[str]) -> list[str]:
    expected_terms = (
        preferences.desired_titles
        + preferences.technologies
        + preferences.work_modes
        + preferences.locations
        + preferences.seniority
        + preferences.required_terms
    )
    normalized_matches = {_normalize(term) for term in matched_terms}
    return _unique_terms(
        [
            _normalize(term)
            for term in expected_terms
            if term.strip() and _normalize(term) not in normalized_matches
        ]
    )


def _classification(score: int) -> str:
    if score >= 80:
        return "Aplicar"
    if score >= 50:
        return "Avaliar"
    return "Ignorar"


def _recommendation_reason(score: int, strengths: list[str], gaps: list[str]) -> str:
    if score >= 80:
        return "Alta aderência aos critérios configurados."
    if score >= 50:
        return "Aderência parcial; revisar gaps antes de decidir."
    if gaps:
        return "Baixa aderência aos critérios configurados."
    return "Poucos dados disponíveis para confirmar aderência."


def _unique_terms(terms: list[str]) -> list[str]:
    seen = set()
    unique = []

    for term in terms:
        normalized = _normalize(term)
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(normalized)

    return unique


def _normalize(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(r"\s+", " ", value).strip().lower()
