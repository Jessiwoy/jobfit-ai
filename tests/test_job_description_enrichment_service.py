import pytest
from core.models import Job
from services.job_description_enrichment_service import (
    JobDescriptionEnrichmentError,
    extract_job_description,
    extract_job_page_details,
    merge_job_descriptions,
    should_enrich_job_description,
)

ENRICHED_DESCRIPTION_HEADER = "Descricao extraida da pagina da vaga"


def test_extract_job_description_prefers_known_description_selector() -> None:
    html = """
    <html>
      <body>
        <nav>Entrar Cadastre-se</nav>
        <section class="jobs-description">
          <h2>Descricao da vaga</h2>
          <p>Responsabilidades: desenvolver interfaces React e integrar APIs REST.</p>
          <p>Requisitos: TypeScript, JavaScript, HTML, CSS, Git e testes.</p>
          <p>Qualificacoes: experiencia em produtos web e comunicacao com times remotos.</p>
          <p>Esta descricao tem conteudo suficiente para alimentar o score com mais contexto
          tecnico do que o alerta de e-mail. Tambem informa atividades, stack e expectativas.</p>
        </section>
      </body>
    </html>
    """

    description = extract_job_description(html)

    assert "Responsabilidades" in description
    assert "TypeScript" in description
    assert "Entrar Cadastre-se" not in description


def test_extract_job_page_details_reads_fields_from_page() -> None:
    html = """
    <html>
      <head><meta property="og:title" content="Frontend Developer"></head>
      <body>
        <h1>Frontend Developer</h1>
        <a class="topcard__org-name-link">Acme</a>
        <span class="topcard__flavor--bullet">Brasil</span>
        <time datetime="2026-06-10T12:00:00Z">2 dias atras</time>
        <section class="jobs-description">
          <h2>Descricao da vaga</h2>
          <p>Responsabilidades: desenvolver interfaces React e integrar APIs REST.</p>
          <p>Requisitos: TypeScript, JavaScript, HTML, CSS, Git e testes.</p>
          <p>Qualificacoes: experiencia em produtos web e comunicacao com times remotos.</p>
          <p>Esta descricao tem conteudo suficiente para alimentar o score com mais contexto
          tecnico do que o alerta de e-mail. Tambem informa atividades, stack e expectativas.</p>
        </section>
      </body>
    </html>
    """

    details = extract_job_page_details(html)

    assert details.title == "Frontend Developer"
    assert details.company == "Acme"
    assert details.location == "Brasil"
    assert details.posted_at == "2026-06-10"
    assert "TypeScript" in details.description


def test_extract_job_description_reports_login_wall_when_no_description_exists() -> None:
    html = """
    <html>
      <body>
        <main>
          <h1>Sign in to view this job</h1>
          <p>Join LinkedIn to access the full job description.</p>
        </main>
      </body>
    </html>
    """

    with pytest.raises(JobDescriptionEnrichmentError, match="exigir login"):
        extract_job_description(html)


def test_merge_job_descriptions_keeps_original_email_context() -> None:
    job = Job(
        id=1,
        source_id=1,
        email_message_id=1,
        title="Frontend Developer",
        description="Resumo extraido do e-mail.",
        content_hash="hash-1",
    )

    merged = merge_job_descriptions(job, "Descricao completa com requisitos React.")

    assert "Resumo extraido do e-mail." in merged
    assert "Descricao extraida da pagina da vaga" in merged
    assert "requisitos React" in merged


def test_should_enrich_job_description_skips_jobs_already_enriched() -> None:
    job = Job(
        id=1,
        source_id=1,
        email_message_id=1,
        title="Frontend Developer",
        job_url="https://example.com/jobs/1",
        description=f"{ENRICHED_DESCRIPTION_HEADER}:\nDescricao completa.",
        posted_at="2026-06-12",
        content_hash="hash-1",
    )

    assert should_enrich_job_description(job) is False


def test_should_enrich_job_description_retries_when_posted_date_is_not_from_page() -> None:
    job = Job(
        id=1,
        source_id=1,
        email_message_id=1,
        title="Frontend Developer",
        job_url="https://example.com/jobs/1",
        description=f"{ENRICHED_DESCRIPTION_HEADER}:\nDescricao completa.",
        posted_at="2026-06-12T10:00:00+00:00",
        content_hash="hash-1",
    )

    assert should_enrich_job_description(job) is True
