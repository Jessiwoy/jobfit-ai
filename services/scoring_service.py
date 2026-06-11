from __future__ import annotations

import re
import unicodedata
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
    cleared_analyses: int = 0


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
            cleared_analyses = self._analyses_repository.delete_all()
            return ScoringSummary(
                reviewed_jobs=len(jobs),
                analyzed_jobs=0,
                skipped_jobs=len(jobs),
                cleared_analyses=cleared_analyses,
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
    desired_title_matches = _matched_title_terms(job, preferences.desired_titles)
    skill_requirements = _matched_terms(job_text, _skill_vocabulary(preferences, profile_items))
    resume_supported_skills = _resume_supported_terms(
        skill_requirements,
        preferences,
        profile_items,
    )
    evidenced_skills = _evidenced_terms(resume_supported_skills, profile_items)
    work_mode_matches = _matched_terms(_normalize(job.work_mode), preferences.work_modes)
    location_matches = _matched_terms(_normalize(job.location), preferences.locations)
    seniority_matches = _matched_terms(_normalize(job.seniority), preferences.seniority)
    required_matches = _matched_terms(job_text, preferences.required_terms)
    undesired_matches = _matched_terms(job_text, preferences.undesired_terms)

    score = 0
    strengths = []
    gaps = []

    score += _coverage_score(
        desired_title_matches,
        preferences.desired_titles,
        weight=20,
        target_matches=1,
    )
    if desired_title_matches:
        strengths.append("Cargo ou função compatível com o alvo profissional.")
    elif preferences.desired_titles:
        gaps.append("Cargo não corresponde claramente aos cargos alvo.")

    score += _coverage_score(
        resume_supported_skills,
        skill_requirements,
        weight=35,
        target_matches=3,
    )
    if resume_supported_skills and profile_items:
        strengths.append("Requisitos técnicos da vaga aparecem nos dados reais do currículo.")
    elif resume_supported_skills:
        strengths.append("Requisitos técnicos da vaga batem com tecnologias configuradas.")
        gaps.append("Cadastre dados reais do currículo para confirmar evidências.")
    elif skill_requirements:
        gaps.append("Requisitos técnicos visíveis na vaga não têm evidência no currículo.")
    elif preferences.technologies or profile_items:
        gaps.append("A vaga não traz requisitos técnicos claros no texto extraído.")

    score += _coverage_score(
        evidenced_skills,
        resume_supported_skills,
        weight=15,
        target_matches=2,
    )
    if evidenced_skills:
        strengths.append("Há evidência contextual de habilidades em experiências ou projetos.")
    elif resume_supported_skills and profile_items:
        gaps.append("Habilidades encontradas sem evidência contextual forte no currículo.")

    score += _coverage_score(
        required_matches,
        preferences.required_terms,
        weight=10,
        target_matches=1,
    )
    if required_matches:
        strengths.append("Termos obrigatórios ou prioritários encontrados.")
    elif preferences.required_terms:
        gaps.append("Termos obrigatórios ou prioritários não aparecem claramente.")

    score += _coverage_score(seniority_matches, preferences.seniority, weight=10, target_matches=1)
    if seniority_matches:
        strengths.append("Senioridade compatível.")
    elif preferences.seniority:
        gaps.append("Senioridade não confirmada como compatível.")

    score += _coverage_score(work_mode_matches, preferences.work_modes, weight=5, target_matches=1)
    if work_mode_matches:
        strengths.append("Modalidade compatível.")
    elif preferences.work_modes:
        gaps.append("Modalidade não confirmada como compatível.")

    score += _coverage_score(location_matches, preferences.locations, weight=5, target_matches=1)
    if location_matches:
        strengths.append("Localização compatível.")
    elif preferences.locations:
        gaps.append("Localização não confirmada como compatível.")

    if undesired_matches:
        score -= 15
        gaps.append("Termos indesejados encontrados.")

    normalized_score = max(0, min(100, round(score)))
    classification = _classification(normalized_score)
    matched_terms = _unique_terms(
        desired_title_matches
        + skill_requirements
        + resume_supported_skills
        + evidenced_skills
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


def _skill_vocabulary(
    preferences: Preferences,
    profile_items: list[ProfileItem],
) -> list[str]:
    profile_skill_terms = [
        item.name
        for item in profile_items
        if item.item_type
        in {
            "technology",
            "skill",
            "experience",
            "project",
            "certification",
            "language",
        }
        and item.name.strip()
    ]
    return _unique_terms(
        preferences.technologies + preferences.required_terms + profile_skill_terms
    )


def _resume_supported_terms(
    job_terms: list[str],
    preferences: Preferences,
    profile_items: list[ProfileItem],
) -> list[str]:
    if not job_terms:
        return []

    resume_text = _profile_text(profile_items)
    if resume_text:
        return _unique_terms(
            [
                term
                for term in job_terms
                if any(variant in resume_text for variant in _term_variants(term))
            ]
        )

    declared_terms = _normalize(" ".join(preferences.technologies + preferences.required_terms))
    return _unique_terms(
        [
            term
            for term in job_terms
            if any(variant in declared_terms for variant in _term_variants(term))
        ]
    )


def _evidenced_terms(job_terms: list[str], profile_items: list[ProfileItem]) -> list[str]:
    evidence_text = _profile_evidence_text(profile_items)
    if not evidence_text:
        return []

    return _unique_terms(
        [
            term
            for term in job_terms
            if any(variant in evidence_text for variant in _term_variants(term))
        ]
    )


def _profile_text(profile_items: list[ProfileItem]) -> str:
    return _normalize(
        " ".join(
            " ".join(
                str(value or "")
                for value in [
                    item.item_type,
                    item.name,
                    item.level,
                    item.years_experience,
                    item.evidence,
                ]
            )
            for item in profile_items
        )
    )


def _profile_evidence_text(profile_items: list[ProfileItem]) -> str:
    evidence_parts = []
    for item in profile_items:
        if item.evidence:
            evidence_parts.append(f"{item.name} {item.evidence}")
        elif item.item_type in {"experience", "project", "certification"}:
            evidence_parts.append(item.name)

    return _normalize(" ".join(evidence_parts))


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


def _coverage_score(
    matches: list[str],
    expected_terms: list[str],
    *,
    weight: int,
    target_matches: int,
) -> float:
    terms = [term for term in expected_terms if term.strip()]
    if not terms:
        return 0

    required_matches = max(1, min(len(terms), target_matches))
    return weight * min(1, len(matches) / required_matches)


def _matched_title_terms(job: Job, desired_titles: list[str]) -> list[str]:
    title_text = _normalize(" ".join([job.title, job.description or ""]))
    direct_matches = _matched_terms(title_text, desired_titles)
    inferred_matches = [
        term
        for term in desired_titles
        if _title_tokens_match(title_text, _normalize(term))
    ]
    return _unique_terms(direct_matches + inferred_matches)


def _title_tokens_match(title_text: str, desired_title: str) -> bool:
    if not desired_title:
        return False

    desired_tokens = _meaningful_tokens(desired_title)
    if not desired_tokens:
        return False

    matched_tokens = [
        token
        for token in desired_tokens
        if any(variant in title_text for variant in _term_variants(token))
    ]

    if {"react", "frontend", "front end", "fullstack", "full stack"} & set(desired_tokens):
        return bool(matched_tokens)

    return len(matched_tokens) >= min(2, len(desired_tokens))


def _meaningful_tokens(value: str) -> set[str]:
    ignored = {"de", "da", "do", "jr", "junior", "pleno", "senior"}
    tokens = {token for token in value.split() if len(token) > 2 and token not in ignored}

    if "front" in tokens and "end" in tokens:
        tokens.add("frontend")
    if "full" in tokens and "stack" in tokens:
        tokens.add("fullstack")

    return tokens


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    matches = []
    for term in terms:
        normalized_term = _normalize(term)
        if not normalized_term:
            continue

        if any(variant in text for variant in _term_variants(normalized_term)):
            matches.append(normalized_term)

    return _unique_terms(matches)


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
    if score >= 70:
        return "Aplicar"
    if score >= 50:
        return "Avaliar"
    return "Ignorar"


def _recommendation_reason(score: int, strengths: list[str], gaps: list[str]) -> str:
    if score >= 70:
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

    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    normalized = re.sub(r"[-_/.,()|]+", " ", without_accents).strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.replace("desenvolvedora", "desenvolvedor")


def _term_variants(term: str) -> set[str]:
    variants = {term}
    synonym_groups = [
        {"frontend", "front end"},
        {"fullstack", "full stack"},
        {"remoto", "remote", "trabalho remoto"},
        {"hibrido", "hybrid"},
        {"presencial", "onsite"},
        {"brasil", "brazil"},
        {"pleno", "mid level"},
        {"junior", "jr"},
    ]

    for group in synonym_groups:
        if term in group:
            variants.update(group)

    if "frontend" in term:
        variants.add(term.replace("frontend", "front end"))
    if "front end" in term:
        variants.add(term.replace("front end", "frontend"))
    if "fullstack" in term:
        variants.add(term.replace("fullstack", "full stack"))
    if "full stack" in term:
        variants.add(term.replace("full stack", "fullstack"))

    return variants
