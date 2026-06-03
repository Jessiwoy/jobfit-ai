from app.streamlit_app import parse_optional_float, parse_profile_items


def test_parse_profile_items_ignores_empty_names() -> None:
    items = parse_profile_items(
        1,
        [
            {
                "Tipo": "technology",
                "Nome": "React",
                "Nivel": "Intermediate",
                "Anos": "1.5",
                "Evidencia": "Built reusable components.",
            },
            {
                "Tipo": "skill",
                "Nome": "",
                "Nivel": "",
                "Anos": "",
                "Evidencia": "",
            },
        ],
    )

    assert len(items) == 1
    assert items[0].name == "React"
    assert items[0].years_experience == 1.5


def test_parse_optional_float_returns_none_for_empty_or_invalid_values() -> None:
    assert parse_optional_float("") is None
    assert parse_optional_float(None) is None
    assert parse_optional_float("invalid") is None
    assert parse_optional_float("2") == 2.0
