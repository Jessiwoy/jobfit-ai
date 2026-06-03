from __future__ import annotations

import streamlit as st
from core.database import get_database_path, initialize_database
from repositories.job_sources_repository import JobSourcesRepository
from repositories.preferences_repository import PreferencesRepository
from repositories.user_repository import UserRepository


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
    st.info("A lista de vagas sera exibida aqui depois da integracao com Gmail.")


def render_settings() -> None:
    st.header("Configuracoes")

    db_path = get_database_path()
    user_repository = UserRepository(db_path)
    preferences_repository = PreferencesRepository(db_path)
    sources_repository = JobSourcesRepository(db_path)

    user = user_repository.get_or_create_default_user()
    preferences = preferences_repository.get_by_user_id(user.id)
    sources_repository.ensure_default_sources()
    sources = sources_repository.list_all()

    with st.form("profile_settings"):
        st.subheader("Perfil profissional")
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

    st.subheader("Fontes de vagas")
    st.dataframe(
        [
            {
                "Fonte": source.name,
                "Label Gmail": source.gmail_label_name,
                "Ativa": "Sim" if source.enabled else "Nao",
                "Parser": source.parser_type,
            }
            for source in sources
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_sync() -> None:
    st.header("Sincronizacao")
    st.info("A sincronizacao com Gmail sera implementada no epico de coleta.")


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


if __name__ == "__main__":
    main()

