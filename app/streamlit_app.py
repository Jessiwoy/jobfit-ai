from __future__ import annotations

import streamlit as st
from core.analysis_models import JobAnalysis
from core.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from core.database import get_database_path, initialize_database
from core.models import Job, JobSource, ProfileItem
from repositories.analyses_repository import AnalysesRepository
from repositories.email_messages_repository import EmailMessagesRepository
from repositories.job_sources_repository import JobSourcesRepository
from repositories.jobs_repository import JobsRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.profile_items_repository import ProfileItemsRepository
from repositories.user_repository import UserRepository
from services.gmail_service import (
    GmailCredentialsMissingError,
    GmailLabelNotFoundError,
    GmailService,
)
from services.gmail_sync_service import GmailSyncService
from services.job_cleanup_service import JobCleanupService
from services.job_processing_service import JobProcessingService
from services.scoring_service import ScoringService

JOB_STATUS_LABELS = {
    "new": "Nova",
    "duplicate": "Duplicada",
    "old": "Antiga",
    "incompatible": "Incompatível",
}

EMAIL_STATUS_LABELS = {
    "new": "Novo",
    "processed": "Processado",
    "error": "Erro",
}

CLASSIFICATION_FILTER_LABELS = ["Sem score", "Aplicar", "Avaliar", "Ignorar"]


def main() -> None:
    st.set_page_config(page_title="JobFit AI", page_icon="JF", layout="wide")

    initialize_database()

    st.title("JobFit AI")
    st.caption("Triagem local de vagas recebidas por alertas de e-mail.")

    page = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Configuracoes", "Sincronizacao"],
    )

    if page == "Dashboard":
        render_dashboard()
    elif page == "Configuracoes":
        render_settings()
    else:
        render_sync()


def render_dashboard() -> None:
    st.header("Dashboard")

    jobs_repository = JobsRepository(get_database_path())
    selected_status_labels = st.multiselect(
        "Status",
        options=list(JOB_STATUS_LABELS.values()),
        default=[JOB_STATUS_LABELS["new"]],
        placeholder="Selecione um ou mais status",
        max_selections=len(JOB_STATUS_LABELS),
    )
    selected_statuses = [
        status
        for status, label in JOB_STATUS_LABELS.items()
        if label in selected_status_labels
    ]

    st.write("Score")
    minimum_score = st.slider(
        "Score mínimo",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    selected_classifications = st.multiselect(
        "Classificação",
        options=CLASSIFICATION_FILTER_LABELS,
        default=CLASSIFICATION_FILTER_LABELS,
        placeholder="Selecione uma ou mais classificações",
        max_selections=len(CLASSIFICATION_FILTER_LABELS),
    )

    jobs = [
        job
        for job in jobs_repository.list_recent(limit=100)
        if job.status in selected_statuses
    ]
    analyses_repository = AnalysesRepository(get_database_path())
    analyses_by_job_id = analyses_repository.list_by_job_ids(
        [job.id for job in jobs if job.id is not None]
    )
    jobs = filter_dashboard_jobs(
        jobs,
        analyses_by_job_id,
        minimum_score=minimum_score,
        selected_classifications=selected_classifications,
    )

    if not jobs:
        st.info("Nenhuma vaga encontrada para os filtros atuais.")
        return

    st.metric("Vagas salvas", jobs_repository.count_all())
    selected_job_id = render_jobs_summary_table(jobs, analyses_by_job_id)
    selected_job = next((job for job in jobs if job.id == selected_job_id), jobs[0])
    render_job_details(selected_job, analyses_by_job_id.get(selected_job.id))


def render_jobs_summary_table(
    jobs: list[Job],
    analyses_by_job_id: dict[int, JobAnalysis],
) -> int | None:
    selected_job_id = st.session_state.get("dashboard_selected_job_id")
    if selected_job_id not in {job.id for job in jobs}:
        selected_job_id = jobs[0].id

    rows = [
        build_dashboard_summary_row(
            job,
            analyses_by_job_id.get(job.id),
            selected=job.id == selected_job_id,
        )
        for job in jobs
    ]
    edited_rows = st.data_editor(
        rows,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("Selecionar"),
            "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100),
            "Classificacao": st.column_config.TextColumn("Classificação"),
            "Cargo": st.column_config.TextColumn("Cargo"),
            "Empresa": st.column_config.TextColumn("Empresa"),
            "Localizacao": st.column_config.TextColumn("Localização"),
            "Status": st.column_config.TextColumn("Status"),
            "ID": None,
        },
        disabled=["Score", "Classificacao", "Cargo", "Empresa", "Localizacao", "Status"],
        hide_index=True,
        use_container_width=True,
        key="dashboard_jobs_table",
    )

    selected_rows = [row for row in edited_rows if row.get("Selecionar")]
    selected_id = int(selected_rows[0]["ID"]) if selected_rows else selected_job_id
    st.session_state["dashboard_selected_job_id"] = selected_id
    return selected_id


def build_dashboard_summary_row(
    job: Job,
    analysis: JobAnalysis | None,
    *,
    selected: bool,
) -> dict[str, object]:
    return {
        "Selecionar": selected,
        "Score": analysis.score if analysis else None,
        "Classificacao": analysis.classification if analysis else "",
        "Cargo": job.title,
        "Empresa": job.company or "",
        "Localizacao": job.location or "",
        "Status": format_job_status(job.status),
        "ID": job.id,
    }


def render_job_details(job: Job, analysis: JobAnalysis | None) -> None:
    st.subheader("Detalhes da vaga")

    st.write(f"**{job.title}**")
    st.caption(" | ".join(item for item in [job.company, job.location, job.provider] if item))

    detail_metrics = st.columns(3)
    detail_metrics[0].metric("Score", analysis.score if analysis else "Sem score")
    detail_metrics[1].metric("Classificação", analysis.classification if analysis else "-")
    detail_metrics[2].metric("Status", format_job_status(job.status))

    if job.job_url:
        st.link_button("Abrir vaga", job.job_url)

    if analysis:
        if analysis.recommendation_reason:
            st.write(f"**Motivo:** {analysis.recommendation_reason}")

        strengths_column, gaps_column = st.columns(2)
        with strengths_column:
            st.write("**Pontos fortes**")
            render_text_list(analysis.strengths, "Nenhum ponto forte calculado.")
        with gaps_column:
            st.write("**Gaps**")
            render_text_list(analysis.gaps, "Nenhum gap calculado.")

        terms_column, missing_column = st.columns(2)
        with terms_column:
            st.write("**Termos encontrados**")
            render_text_list(analysis.matched_terms, "Nenhum termo encontrado.")
        with missing_column:
            st.write("**Termos ausentes**")
            render_text_list(analysis.missing_terms, "Nenhum termo ausente.")
    else:
        st.info("Esta vaga ainda nao possui score calculado.")

    if job.description:
        with st.expander("Descrição"):
            st.write(job.description)


def render_text_list(items: list[str], empty_message: str) -> None:
    cleaned_items = [item.strip() for item in items if item.strip()]
    if not cleaned_items:
        st.caption(empty_message)
        return

    for item in cleaned_items:
        st.markdown(f"- {item}")


def render_settings() -> None:
    st.header("Configuracoes")

    db_path = get_database_path()
    user_repository = UserRepository(db_path)
    preferences_repository = PreferencesRepository(db_path)
    profile_items_repository = ProfileItemsRepository(db_path)
    sources_repository = JobSourcesRepository(db_path)

    user = user_repository.get_or_create_default_user()
    preferences = preferences_repository.get_by_user_id(user.id)
    profile_items = profile_items_repository.list_by_user_id(user.id)
    sources_repository.ensure_default_sources()
    sources = sources_repository.list_all()

    profile_tab, resume_data_tab, sources_tab = st.tabs(
        ["Perfil e preferencias", "Dados reais do curriculo", "Label de coleta"]
    )

    with profile_tab:
        render_profile_form(user_repository, preferences_repository, user, preferences)

    with resume_data_tab:
        render_profile_items_editor(profile_items_repository, user.id, profile_items)

    with sources_tab:
        render_job_sources_table(sources_repository, sources)


def render_profile_form(
    user_repository: UserRepository,
    preferences_repository: PreferencesRepository,
    user,
    preferences,
) -> None:  # type: ignore[no-untyped-def]
    with st.form("profile_settings"):
        name = st.text_input("Nome", value=user.name or "")
        email = st.text_input("E-mail profissional", value=user.email or "")
        current_title = st.text_input("Cargo atual ou alvo", value=user.current_title or "")
        location = st.text_input("Localizacao", value=user.location or "")
        summary = st.text_area("Resumo profissional", value=user.summary or "", height=120)

        st.subheader("Preferencias")
        desired_titles = st.text_area(
            "Cargos desejados",
            value="\n".join(preferences.desired_titles),
            help="Informe um item por linha.",
        )
        seniority = st.text_area(
            "Senioridade",
            value="\n".join(preferences.seniority),
            help="Informe um item por linha.",
        )
        technologies = st.text_area(
            "Tecnologias",
            value="\n".join(preferences.technologies),
            help="Informe um item por linha.",
        )
        work_modes = st.text_area(
            "Modalidades",
            value="\n".join(preferences.work_modes),
            help="Informe um item por linha.",
        )
        locations = st.text_area(
            "Localizacoes aceitas",
            value="\n".join(preferences.locations),
            help="Informe um item por linha.",
        )
        required_terms = st.text_area(
            "Termos obrigatorios",
            value="\n".join(preferences.required_terms),
            help="Informe um item por linha.",
        )
        undesired_terms = st.text_area(
            "Termos indesejados",
            value="\n".join(preferences.undesired_terms),
            help="Informe um item por linha.",
        )

        submitted = st.form_submit_button("Salvar configuracoes")

    if submitted:
        user_repository.update_profile(
            user_id=user.id,
            name=name,
            email=email,
            current_title=current_title,
            location=location,
            summary=summary,
        )
        preferences_repository.upsert(
            user_id=user.id,
            desired_titles=parse_lines(desired_titles),
            seniority=parse_lines(seniority),
            technologies=parse_lines(technologies),
            work_modes=parse_lines(work_modes),
            locations=parse_lines(locations),
            required_terms=parse_lines(required_terms),
            undesired_terms=parse_lines(undesired_terms),
        )
        st.success("Configuracoes salvas.")


def render_profile_items_editor(
    repository: ProfileItemsRepository,
    user_id: int,
    profile_items: list[ProfileItem],
) -> None:
    st.caption(
        "Cadastre apenas informacoes reais. Esses dados serao a base para score e materiais."
    )

    rows = [
        {
            "Tipo": item.item_type,
            "Nome": item.name,
            "Nivel": item.level or "",
            "Anos": item.years_experience,
            "Evidencia": item.evidence or "",
        }
        for item in profile_items
    ]

    edited_rows = st.data_editor(
        rows,
        column_config={
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo",
                options=[
                    "technology",
                    "skill",
                    "experience",
                    "project",
                    "education",
                    "certification",
                    "language",
                ],
                required=True,
            ),
            "Nome": st.column_config.TextColumn("Nome", required=True),
            "Nivel": st.column_config.TextColumn("Nivel"),
            "Anos": st.column_config.NumberColumn("Anos", min_value=0.0, step=0.5),
            "Evidencia": st.column_config.TextColumn("Evidencia"),
        },
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="profile_items_editor",
    )

    if st.button("Salvar dados reais do curriculo"):
        repository.replace_for_user(user_id, parse_profile_items(user_id, edited_rows))
        st.success("Dados reais do curriculo salvos.")


def render_job_sources_table(
    sources_repository: JobSourcesRepository,
    sources: list[JobSource],
) -> None:
    st.caption("Configure a label unica do Gmail que recebera todos os alertas de vagas.")

    rows = [
        {
            "Nome": source.name,
            "Label Gmail": source.gmail_label_name,
            "Ativa": source.enabled,
        }
        for source in sources
    ]

    edited_rows = st.data_editor(
        rows,
        column_config={
            "Nome": st.column_config.TextColumn("Nome", required=True),
            "Label Gmail": st.column_config.TextColumn("Label Gmail", required=True),
            "Ativa": st.column_config.CheckboxColumn("Ativa"),
        },
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="job_sources_editor",
    )

    if st.button("Salvar label de coleta"):
        parsed_sources = parse_job_sources(edited_rows)
        if not parsed_sources:
            st.error("Informe ao menos uma fonte com nome e label.")
            return

        sources_repository.replace_all(parsed_sources)
        st.success("Label de coleta salva.")


def render_sync() -> None:
    st.header("Sincronizacao")

    db_path = get_database_path()
    sources_repository = JobSourcesRepository(db_path)
    messages_repository = EmailMessagesRepository(db_path)
    jobs_repository = JobsRepository(db_path)
    analyses_repository = AnalysesRepository(db_path)
    sources_repository.ensure_default_sources()
    active_sources = [source for source in sources_repository.list_all() if source.enabled]

    st.subheader("Gmail")
    st.write(f"Credenciais: `{GMAIL_CREDENTIALS_PATH}`")
    st.write(f"Token local: `{GMAIL_TOKEN_PATH}`")

    if GMAIL_CREDENTIALS_PATH.exists():
        st.success("Arquivo de credenciais encontrado.")
    else:
        st.warning("Arquivo de credenciais ainda nao encontrado.")

    st.subheader("Label ativa")
    if not active_sources:
        st.info("Nenhuma fonte ativa configurada.")
        return

    st.dataframe(
        [
            {
                "Fonte": source.name,
                "Label Gmail": source.gmail_label_name,
            }
            for source in active_sources
        ],
        hide_index=True,
        use_container_width=True,
    )

    if st.button("Validar labels no Gmail"):
        validate_gmail_labels(active_sources)

    st.subheader("Coleta")
    max_results = st.number_input(
        "Limite de e-mails por label",
        min_value=1,
        max_value=100,
        value=25,
        step=5,
    )

    if st.button("Buscar novos e-mails"):
        sync_gmail_messages(int(max_results))

    email_metric, pending_metric, error_metric, jobs_metric, analyses_metric = st.columns(5)
    email_metric.metric("E-mails salvos", messages_repository.count_all())
    pending_metric.metric("E-mails novos", messages_repository.count_by_status("new"))
    error_metric.metric("E-mails com erro", messages_repository.count_by_status("error"))
    jobs_metric.metric("Vagas criadas", jobs_repository.count_all())
    analyses_metric.metric("Scores calculados", analyses_repository.count_all())

    job_status_metrics = st.columns(4)
    job_status_metrics[0].metric("Vagas novas", count_jobs_by_status(jobs_repository, "new"))
    job_status_metrics[1].metric("Duplicadas", count_jobs_by_status(jobs_repository, "duplicate"))
    job_status_metrics[2].metric("Antigas", count_jobs_by_status(jobs_repository, "old"))
    job_status_metrics[3].metric(
        "Incompatíveis",
        count_jobs_by_status(jobs_repository, "incompatible"),
    )

    st.subheader("Processamento")
    process_limit = st.number_input(
        "Limite de e-mails para processar",
        min_value=1,
        max_value=100,
        value=50,
        step=5,
    )

    if st.button("Processar e-mails salvos"):
        process_saved_emails(int(process_limit))

    if st.button("Reprocessar e-mails com erro"):
        reprocess_failed_emails(int(process_limit))

    st.subheader("Limpeza")
    max_age_days = st.number_input(
        "Idade maxima da vaga em dias",
        min_value=1,
        max_value=365,
        value=45,
        step=5,
    )

    if st.button("Limpar e deduplicar vagas"):
        cleanup_jobs(int(max_age_days))

    st.subheader("Score")
    render_scoring_criteria_summary()
    render_score_analysis_summary(analyses_repository)

    if st.button("Recalcular scores"):
        score_jobs()

    st.subheader("Ultimos e-mails")
    recent_messages = messages_repository.list_recent(limit=10)

    if recent_messages:
        st.dataframe(
            [
                {
                    "Recebido em": message.received_at or "",
                    "Assunto": message.subject or "",
                    "Remetente": message.sender or "",
                    "Label": message.gmail_label_name,
                    "Provedor": message.detected_provider or "",
                    "Status": format_email_status(message.processed_status),
                    "Erro": message.error_message or "",
                }
                for message in recent_messages
            ],
            hide_index=True,
            use_container_width=True,
        )


def validate_gmail_labels(active_sources: list[JobSource]) -> None:
    label_names = [source.gmail_label_name for source in active_sources]

    try:
        results = GmailService().validate_labels(label_names)
    except GmailCredentialsMissingError as error:
        st.error(str(error))
        return
    except Exception as error:  # pragma: no cover - defensive UI boundary
        st.error(f"Nao foi possivel validar as labels: {error}")
        return

    st.dataframe(
        [
            {
                "Label Gmail": result.label_name,
                "Encontrada": "Sim" if result.exists else "Nao",
                "ID": result.label_id or "",
            }
            for result in results
        ],
        hide_index=True,
        use_container_width=True,
    )


def sync_gmail_messages(max_results_per_source: int) -> None:
    try:
        summary = GmailSyncService(get_database_path()).sync_active_sources(
            max_results_per_source=max_results_per_source
        )
    except GmailCredentialsMissingError as error:
        st.error(str(error))
        return
    except GmailLabelNotFoundError as error:
        st.error(str(error))
        return
    except Exception as error:  # pragma: no cover - defensive UI boundary
        st.error(f"Nao foi possivel sincronizar o Gmail: {error}")
        return

    if not summary.results:
        st.info("Nenhuma fonte ativa configurada.")
        return

    st.success(f"Sincronizacao concluida. {summary.inserted_count} e-mail(s) novo(s) salvo(s).")
    if summary.failed_count:
        st.warning(f"{summary.failed_count} fonte(s) tiveram erro durante a sincronizacao.")

    st.dataframe(
        [
            {
                "Fonte": result.source_name,
                "Label Gmail": result.label_name,
                "Status": "Erro" if result.error_message else "OK",
                "Novos encontrados": result.fetched_count,
                "Salvos": result.inserted_count,
                "Ignorados": result.skipped_count,
                "Erro": result.error_message or "",
            }
            for result in summary.results
        ],
        hide_index=True,
        use_container_width=True,
    )


def process_saved_emails(limit: int) -> None:
    summary = JobProcessingService(get_database_path()).process_new_messages(limit=limit)

    if summary.processed_messages == 0:
        st.info("Nao ha e-mails novos para processar.")
        return

    st.success(
        "Processamento concluido. "
        f"{summary.created_jobs} vaga(s) criada(s), "
        f"{summary.failed_messages} erro(s)."
    )


def reprocess_failed_emails(limit: int) -> None:
    summary = JobProcessingService(get_database_path()).reprocess_failed_messages(limit=limit)

    if summary.processed_messages == 0:
        st.info("Nao ha e-mails com erro para reprocessar.")
        return

    st.success(
        "Reprocessamento concluido. "
        f"{summary.created_jobs} vaga(s) criada(s), "
        f"{summary.failed_messages} erro(s)."
    )


def cleanup_jobs(max_age_days: int) -> None:
    summary = JobCleanupService(get_database_path()).cleanup_jobs(max_age_days=max_age_days)

    if summary.reviewed_jobs == 0:
        st.info("Nao ha vagas para limpar.")
        return

    st.success(
        "Limpeza concluida. "
        f"{summary.duplicate_jobs} duplicada(s), "
        f"{summary.old_jobs} antiga(s), "
        f"{summary.incompatible_jobs} incompatível(is)."
    )


def score_jobs() -> None:
    summary = ScoringService(get_database_path()).score_new_jobs()

    if summary.reviewed_jobs == 0:
        st.info("Nao ha vagas novas para calcular score.")
        return

    if summary.analyzed_jobs == 0:
        if summary.cleared_analyses:
            st.warning(
                "Configure perfil, preferencias ou dados reais antes de calcular scores. "
                f"{summary.cleared_analyses} score(s) antigo(s) foram limpos."
            )
            return

        st.warning("Configure perfil, preferencias ou dados reais antes de calcular scores.")
        return

    st.success(f"Score recalculado para {summary.analyzed_jobs} vaga(s).")


def render_scoring_criteria_summary() -> None:
    summary = ScoringService(get_database_path()).get_criteria_summary()

    criteria_metrics = st.columns(4)
    criteria_metrics[0].metric("Cargos", summary.desired_titles)
    criteria_metrics[1].metric("Tecnologias", summary.technologies)
    criteria_metrics[2].metric("Modalidades", summary.work_modes)
    criteria_metrics[3].metric("Dados reais", summary.profile_items)

    if not summary.can_score:
        st.warning(
            "Configure perfil, preferências ou dados reais antes de calcular scores."
        )


def render_score_analysis_summary(analyses_repository: AnalysesRepository) -> None:
    if analyses_repository.count_all() == 0:
        return

    st.write("Resumo dos scores calculados")
    classification_counts = analyses_repository.count_by_classification()
    score_range_counts = analyses_repository.count_by_score_range()

    classification_columns = st.columns(3)
    classification_columns[0].metric("Aplicar", classification_counts.get("Aplicar", 0))
    classification_columns[1].metric("Avaliar", classification_counts.get("Avaliar", 0))
    classification_columns[2].metric("Ignorar", classification_counts.get("Ignorar", 0))

    range_columns = st.columns(3)
    range_columns[0].metric("Score 0-49", score_range_counts.get("0-49", 0))
    range_columns[1].metric("Score 50-79", score_range_counts.get("50-79", 0))
    range_columns[2].metric("Score 80-100", score_range_counts.get("80-100", 0))


def format_job_status(status: str) -> str:
    return JOB_STATUS_LABELS.get(status, status)


def format_email_status(status: str) -> str:
    return EMAIL_STATUS_LABELS.get(status, status)


def count_jobs_by_status(repository: JobsRepository, status: str) -> int:
    count_by_status = getattr(repository, "count_by_status", None)
    if callable(count_by_status):
        return int(count_by_status(status))

    return sum(1 for job in repository.list_recent(limit=10000) if job.status == status)


def filter_dashboard_jobs(
    jobs: list[Job],
    analyses_by_job_id: dict[int, JobAnalysis],
    *,
    minimum_score: int,
    selected_classifications: list[str],
) -> list[Job]:
    filtered_jobs = []
    include_without_score = "Sem score" in selected_classifications

    for job in jobs:
        if job.id is None:
            continue

        analysis = analyses_by_job_id.get(job.id)
        if analysis is None:
            if include_without_score and minimum_score == 0:
                filtered_jobs.append(job)
            continue

        if analysis.score < minimum_score:
            continue

        if analysis.classification not in selected_classifications:
            continue

        filtered_jobs.append(job)

    return filtered_jobs


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def parse_profile_items(user_id: int, rows: list[dict]) -> list[ProfileItem]:
    items = []

    for row in rows:
        name = str(row.get("Nome") or "").strip()
        if not name:
            continue

        item_type = str(row.get("Tipo") or "skill").strip()
        level = str(row.get("Nivel") or "").strip() or None
        evidence = str(row.get("Evidencia") or "").strip() or None
        years_experience = parse_optional_float(row.get("Anos"))

        items.append(
            ProfileItem(
                id=None,
                user_id=user_id,
                item_type=item_type,
                name=name,
                level=level,
                years_experience=years_experience,
                evidence=evidence,
            )
        )

    return items


def parse_job_sources(rows: list[dict]) -> list[JobSource]:
    sources = []

    for row in rows:
        name = str(row.get("Nome") or "").strip()
        gmail_label_name = str(row.get("Label Gmail") or "").strip()
        if not name or not gmail_label_name:
            continue

        sources.append(
            JobSource(
                id=0,
                name=name,
                gmail_label_name=gmail_label_name,
                source_type="gmail_label",
                parser_type="generic",
                enabled=bool(row.get("Ativa", True)),
            )
        )

    return sources


def parse_optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
