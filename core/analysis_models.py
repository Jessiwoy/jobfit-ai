from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JobAnalysis:
    id: int | None
    job_id: int
    score: int
    classification: str
    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    recommendation_reason: str | None = None
    matched_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)
    undesired_terms_found: list[str] = field(default_factory=list)
