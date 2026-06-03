import sqlite3


def test_runtime_dependencies_are_available() -> None:
    import bs4
    import googleapiclient.discovery
    import pydantic
    import streamlit

    assert bs4 is not None
    assert googleapiclient.discovery is not None
    assert pydantic is not None
    assert streamlit is not None


def test_sqlite_is_available() -> None:
    assert sqlite3.sqlite_version
