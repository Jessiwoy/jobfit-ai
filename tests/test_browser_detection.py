from pathlib import Path

from services.browser_detection import (
    _extract_executable_path,
    get_preferred_browser_launch_config,
)


def test_extract_executable_path_from_quoted_windows_command() -> None:
    command = r'"C:\Users\User\AppData\Local\Programs\Opera\opera.exe" "%1"'

    assert _extract_executable_path(command) == (
        r"C:\Users\User\AppData\Local\Programs\Opera\opera.exe"
    )


def test_extract_executable_path_from_unquoted_windows_command() -> None:
    command = r"C:\Program Files\Google\Chrome\Application\chrome.exe --single-argument %1"

    assert _extract_executable_path(command) == (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    )


def test_browser_executable_env_override(monkeypatch, tmp_path: Path) -> None:
    executable = tmp_path / "opera.exe"
    executable.write_text("", encoding="utf-8")
    monkeypatch.setenv("JOBFIT_BROWSER_EXECUTABLE", str(executable))

    config = get_preferred_browser_launch_config()

    assert config.executable_path == str(executable)
    assert config.display_name == "Opera"
