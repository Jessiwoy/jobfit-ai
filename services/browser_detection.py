from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BrowserLaunchConfig:
    executable_path: str | None
    display_name: str


def get_preferred_browser_launch_config() -> BrowserLaunchConfig:
    configured_path = os.environ.get("JOBFIT_BROWSER_EXECUTABLE")
    if configured_path and Path(configured_path).exists():
        return BrowserLaunchConfig(
            executable_path=configured_path,
            display_name=_browser_name_from_path(configured_path),
        )

    if sys.platform == "win32":
        executable_path = _windows_default_https_browser_path()
        if executable_path and Path(executable_path).exists():
            return BrowserLaunchConfig(
                executable_path=executable_path,
                display_name=_browser_name_from_path(executable_path),
            )

    return BrowserLaunchConfig(
        executable_path=None,
        display_name="Chromium do Playwright",
    )


def launch_persistent_chromium_context(
    playwright,  # type: ignore[no-untyped-def]
    user_data_dir: Path,
    **kwargs,  # type: ignore[no-untyped-def]
):
    browser_config = get_preferred_browser_launch_config()
    try:
        return playwright.chromium.launch_persistent_context(
            str(user_data_dir),
            executable_path=browser_config.executable_path,
            **kwargs,
        )
    except Exception:
        if browser_config.executable_path is None:
            raise

        return playwright.chromium.launch_persistent_context(
            str(user_data_dir),
            **kwargs,
        )


def _windows_default_https_browser_path() -> str | None:
    try:
        import winreg
    except ImportError:
        return None

    prog_id = _read_registry_value(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        "ProgId",
    )
    if not prog_id:
        return None

    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        command = _read_registry_value(
            root,
            rf"Software\Classes\{prog_id}\shell\open\command",
            "",
        )
        executable_path = _extract_executable_path(command or "")
        if executable_path:
            return executable_path

    return None


def _read_registry_value(root, path: str, name: str) -> str | None:  # type: ignore[no-untyped-def]
    try:
        import winreg

        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return None


def _extract_executable_path(command: str) -> str | None:
    quoted_match = re.search(r'"([^"]+\.exe)"', command, flags=re.IGNORECASE)
    if quoted_match:
        return quoted_match.group(1)

    unquoted_match = re.search(r"([A-Za-z]:\\.+?\.exe)", command, flags=re.IGNORECASE)
    if unquoted_match:
        return unquoted_match.group(1)

    return None


def _browser_name_from_path(executable_path: str) -> str:
    name = Path(executable_path).stem.lower()
    labels = {
        "opera": "Opera",
        "opera_browser": "Opera",
        "chrome": "Google Chrome",
        "msedge": "Microsoft Edge",
        "brave": "Brave",
        "vivaldi": "Vivaldi",
        "firefox": "Firefox",
        "iexplore": "Internet Explorer",
    }
    return labels.get(name, Path(executable_path).name)
