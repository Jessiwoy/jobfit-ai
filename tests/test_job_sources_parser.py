from app.streamlit_app import parse_job_sources


def test_parse_job_sources_ignores_rows_without_name_or_label() -> None:
    sources = parse_job_sources(
        [
            {
                "Nome": "Job Alerts",
                "Label Gmail": "Job Alerts",
                "Ativa": True,
            },
            {
                "Nome": "",
                "Label Gmail": "Missing Name Jobs",
                "Ativa": True,
                "Parser": "generic",
            },
            {
                "Nome": "Missing Label",
                "Label Gmail": "",
                "Ativa": True,
                "Parser": "generic",
            },
        ]
    )

    assert len(sources) == 1
    assert sources[0].name == "Job Alerts"
    assert sources[0].gmail_label_name == "Job Alerts"
    assert sources[0].parser_type == "generic"


def test_parse_job_sources_defaults_parser_to_generic() -> None:
    sources = parse_job_sources(
        [
            {
                "Nome": "Custom",
                "Label Gmail": "Custom Jobs",
                "Ativa": False,
            }
        ]
    )

    assert sources[0].parser_type == "generic"
    assert sources[0].enabled is False
