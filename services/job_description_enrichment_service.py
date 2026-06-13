from __future__ import annotations

import re
import unicodedata
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup
from core.models import Job
from repositories.jobs_repository import JobsRepository

DESCRIPTION_SELECTORS = [
    "div.jobs-description__content",
    "div.jobs-box__html-content",
    "section.jobs-description",
    "div.description__text",
    "div[data-test-id*='job-description']",
    "div[data-test-id*='job-details']",
    "#job-details",
]

DESCRIPTION_KEYWORDS = [
    "descricao da vaga",
    "descrição da vaga",
    "responsabilidades",
    "requisitos",
    "qualificacoes",
    "qualificações",
    "atribuições",
    "about the job",
    "job description",
    "responsibilities",
    "requirements",
    "qualifications",
    "skills",
]

LOGIN_WALL_TERMS = [
    "sign in",
    "join linkedin",
    "acesse sua conta",
    "authwall",
    "login to view",
]

ENRICHED_DESCRIPTION_HEADER = "Descricao extraida da pagina da vaga"


class JobDescriptionEnrichmentError(RuntimeError):
    pass


@dataclass(frozen=True)
class JobDescriptionEnrichmentResult:
    job_id: int
    previous_length: int
    enriched_length: int
    description: str


@dataclass(frozen=True)
class JobDescriptionEnrichmentBatchSummary:
    attempted_jobs: int
    enriched_jobs: int
    failed_jobs: int
    errors: list[str]
    login_required: bool = False


@dataclass(frozen=True)
class ExtractedJobPageDetails:
    title: str | None
    company: str | None
    location: str | None
    posted_at: str | None
    description: str


class JobDescriptionEnrichmentService:
    def __init__(
        self,
        database_path: Path,
        *,
        user_data_dir: Path | None = None,
        cdp_url: str | None = None,
    ) -> None:
        self._jobs_repository = JobsRepository(database_path)
        self._user_data_dir = user_data_dir or Path("data") / "playwright-profile"
        self._cdp_url = cdp_url

    def enrich_job(self, job_id: int) -> JobDescriptionEnrichmentResult:
        job = self._jobs_repository.get_by_id(job_id)
        if job is None:
            raise JobDescriptionEnrichmentError("Vaga nao encontrada.")
        if not job.job_url:
            raise JobDescriptionEnrichmentError("Esta vaga nao possui link para enriquecer.")

        page_details = self._fetch_page_details(job.job_url)
        description = merge_job_descriptions(job, page_details.description)
        self._jobs_repository.update_details_from_page(
            job_id,
            title=page_details.title,
            company=page_details.company,
            location=page_details.location,
            posted_at=page_details.posted_at,
            description=description,
        )

        return JobDescriptionEnrichmentResult(
            job_id=job_id,
            previous_length=len(job.description or ""),
            enriched_length=len(description),
            description=description,
        )

    def enrich_jobs(self, jobs: list[Job]) -> JobDescriptionEnrichmentBatchSummary:
        candidates = [job for job in jobs if should_enrich_job_description(job)]
        if not candidates:
            return JobDescriptionEnrichmentBatchSummary(
                attempted_jobs=0,
                enriched_jobs=0,
                failed_jobs=0,
                errors=[],
                login_required=False,
            )

        errors = []
        enriched_jobs = 0
        login_required = False

        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise JobDescriptionEnrichmentError(
                "Playwright nao esta instalado. Rode: "
                ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt "
                "e depois .\\.venv\\Scripts\\python.exe -m playwright install chromium"
            ) from error

        with sync_playwright() as playwright:
            browser = None
            context = None
            try:
                if self._cdp_url:
                    browser = playwright.chromium.connect_over_cdp(self._cdp_url)
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                else:
                    context = playwright.chromium.launch_persistent_context(
                        str(self._user_data_dir),
                        headless=False,
                        viewport={"width": 1366, "height": 900},
                    )

                for job in candidates:
                    if job.id is None or not job.job_url:
                        continue

                    page = None
                    try:
                        page = context.new_page()
                        page.goto(job.job_url, wait_until="domcontentloaded", timeout=45000)
                        with suppress(PlaywrightTimeoutError):
                            page.wait_for_load_state("networkidle", timeout=10000)

                        page_details = extract_job_page_details(page.content())
                        description = merge_job_descriptions(job, page_details.description)
                        self._jobs_repository.update_details_from_page(
                            job.id,
                            title=page_details.title,
                            company=page_details.company,
                            location=page_details.location,
                            posted_at=page_details.posted_at,
                            description=description,
                        )
                        enriched_jobs += 1
                    except Exception as error:  # pragma: no cover - browser-dependent boundary
                        if _is_login_required_error(error):
                            login_required = True
                        errors.append(f"{job.title}: {error}")
                    finally:
                        if page is not None:
                            page.close()
            finally:
                if self._cdp_url and browser is not None:
                    browser.close()
                elif context is not None:
                    context.close()

        return JobDescriptionEnrichmentBatchSummary(
            attempted_jobs=len(candidates),
            enriched_jobs=enriched_jobs,
            failed_jobs=len(candidates) - enriched_jobs,
            errors=errors,
            login_required=login_required,
        )

    def _fetch_page_details(self, url: str) -> ExtractedJobPageDetails:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise JobDescriptionEnrichmentError(
                "Playwright nao esta instalado. Rode: "
                ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt "
                "e depois .\\.venv\\Scripts\\python.exe -m playwright install chromium"
            ) from error

        with sync_playwright() as playwright:
            browser = None
            context = None
            page = None
            try:
                if self._cdp_url:
                    browser = playwright.chromium.connect_over_cdp(self._cdp_url)
                    context = browser.contexts[0] if browser.contexts else browser.new_context()
                else:
                    context = playwright.chromium.launch_persistent_context(
                        str(self._user_data_dir),
                        headless=False,
                        viewport={"width": 1366, "height": 900},
                    )

                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                with suppress(PlaywrightTimeoutError):
                    page.wait_for_load_state("networkidle", timeout=10000)

                page_html = page.content()
            finally:
                if page is not None:
                    page.close()
                if self._cdp_url and browser is not None:
                    browser.close()
                elif context is not None:
                    context.close()

        return extract_job_page_details(page_html)

    def _fetch_page_description(self, url: str) -> str:
        return self._fetch_page_details(url).description


def merge_job_descriptions(job: Job, page_description: str) -> str:
    existing_description = (job.description or "").strip()
    page_description = page_description.strip()

    parts = [
        existing_description,
        f"{ENRICHED_DESCRIPTION_HEADER}:\n{page_description}",
    ]
    return "\n\n---\n\n".join(part for part in parts if part)[:12000]


def should_enrich_job_description(job: Job) -> bool:
    if job.id is None or not job.job_url:
        return False

    if ENRICHED_DESCRIPTION_HEADER not in (job.description or ""):
        return True

    return not _has_reliable_posted_at(job.posted_at)


def extract_job_page_details(html: str) -> ExtractedJobPageDetails:
    soup = _clean_soup(html)
    description = extract_job_description_from_soup(soup)
    full_text = _clean_text(soup.get_text("\n", strip=True))

    return ExtractedJobPageDetails(
        title=_first_selector_text(
            soup,
            [
                "h1",
                ".top-card-layout__title",
                ".jobs-unified-top-card__job-title",
                "[data-testid='jobsearch-JobInfoHeader-title']",
            ],
        )
        or _meta_content(soup, "og:title"),
        company=_first_selector_text(
            soup,
            [
                ".topcard__org-name-link",
                ".jobs-unified-top-card__company-name",
                "[data-testid='inlineHeader-companyName']",
                "[data-company-name]",
            ],
        ),
        location=_first_selector_text(
            soup,
            [
                ".topcard__flavor--bullet",
                ".jobs-unified-top-card__bullet",
                "[data-testid='job-location']",
            ],
        ),
        posted_at=extract_posted_at_from_page(soup, full_text),
        description=description,
    )


def extract_job_description(html: str) -> str:
    soup = _clean_soup(html)
    return extract_job_description_from_soup(soup)


def extract_job_description_from_soup(soup: BeautifulSoup) -> str:
    full_text = _clean_text(soup.get_text("\n", strip=True))
    if _looks_like_login_wall(full_text):
        raise JobDescriptionEnrichmentError(
            "A pagina parece exigir login. Faca login no navegador aberto e recalcule."
        )

    selector_texts = [
        _clean_text(element.get_text("\n", strip=True))
        for selector in DESCRIPTION_SELECTORS
        for element in soup.select(selector)
    ]
    candidates = [text for text in selector_texts if _looks_like_description(text)]

    if not candidates:
        candidates = _keyword_candidates(soup)

    if not candidates:
        raise JobDescriptionEnrichmentError(
            "Nao encontrei um bloco de descricao confiavel nessa pagina."
        )

    return max(candidates, key=len)[:8000]


def _clean_soup(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()
    return soup


def extract_posted_at_from_page(soup: BeautifulSoup, full_text: str) -> str | None:
    for time_element in soup.select("time"):
        datetime_value = time_element.get("datetime")
        parsed = _parse_absolute_date(str(datetime_value or ""))
        if parsed:
            return parsed

        parsed = _parse_relative_date(time_element.get_text(" ", strip=True))
        if parsed:
            return parsed

    return _parse_relative_date(full_text)


def _keyword_candidates(soup: BeautifulSoup) -> list[str]:
    candidates = []
    for element in soup.find_all(["main", "section", "article", "div"]):
        text = _clean_text(element.get_text("\n", strip=True))
        if _looks_like_description(text):
            candidates.append(text)

    return candidates


def _looks_like_description(text: str) -> bool:
    normalized = _normalize(text)
    if len(normalized) < 300:
        return False

    return any(keyword in normalized for keyword in DESCRIPTION_KEYWORDS)


def _first_selector_text(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        element = soup.select_one(selector)
        if element is None:
            continue

        text = _clean_text(element.get_text(" ", strip=True))
        if text:
            return text[:180]

    return None


def _meta_content(soup: BeautifulSoup, property_name: str) -> str | None:
    element = soup.find("meta", attrs={"property": property_name})
    if element is None:
        return None

    content = str(element.get("content") or "").strip()
    return content[:180] or None


def _parse_absolute_date(value: str) -> str | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass

    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    if match:
        return match.group(1)

    return None


def _has_reliable_posted_at(value: str | None) -> bool:
    if not value:
        return False

    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value.strip()))


def _parse_relative_date(value: str) -> str | None:
    normalized = _normalize(value)
    today = date.today()
    if re.search(r"\b(hoje|today|recem publicada|recem publicado|just posted)\b", normalized):
        return today.isoformat()

    match = re.search(r"\b(?:ha|posted|publicada ha|publicado ha)?\s*(\d+)\s+dia", normalized)
    if match:
        return (today - timedelta(days=int(match.group(1)))).isoformat()

    match = re.search(r"\b(\d+)\s+day", normalized)
    if match:
        return (today - timedelta(days=int(match.group(1)))).isoformat()

    return None


def _looks_like_login_wall(text: str) -> bool:
    normalized = _normalize(text)
    return any(term in normalized for term in LOGIN_WALL_TERMS)


def _is_login_required_error(error: Exception) -> bool:
    return "exigir login" in str(error).lower()


def _clean_text(value: str) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text)


def _normalize(value: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()
