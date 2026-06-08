from __future__ import annotations

import streamlit as st
from core.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from core.database import get_database_path, initialize_database
from core.models import JobSource, ProfileItem
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
from services.job_processing_service import JobProcessingService


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
    jobs = jobs_repository.list_recent(limit=100)

    if not jobs:
        st.info("Nenhuma vaga salva ainda. Sincronize e processe e-mails para popular o dashboard.")
        return

    st.metric("Vagas salvas", jobs_repository.count_all())
    st.dataframe(
        [
            {
                "Cargo": job.title,
                "Empresa": job.company or "",
                "Localizacao": job.location or "",
                "Modalidade": job.work_mode or "",
                "Senioridade": job.seniority or "",
                "Provedor": job.provider or "",
                "Status": job.status,
                "Link": job.job_url or "",
            }
            for job in jobs
        ],
        hide_index=True,
        use_container_width=True,
    )


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

    email_metric, pending_metric, jobs_metric = st.columns(3)
    email_metric.metric("E-mails salvos", messages_repository.count_all())
    pending_metric.metric("E-mails novos", messages_repository.count_by_status("new"))
    jobs_metric.metric("Vagas criadas", jobs_repository.count_all())

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
                    "Status": message.processed_status,
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
    st.dataframe(
        [
            {
                "Fonte": result.source_name,
                "Label Gmail": result.label_name,
                "Novos encontrados": result.fetched_count,
                "Salvos": result.inserted_count,
                "Ignorados": result.skipped_count,
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
