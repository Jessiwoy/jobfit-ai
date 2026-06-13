from __future__ import annotations

import time

from core.config import ROOT_DIR
from playwright.sync_api import sync_playwright

LOGIN_URLS = [
    "https://www.linkedin.com/login",
    "https://secure.indeed.com/auth",
    "https://www.glassdoor.com/profile/login_input.htm",
]


def main() -> None:
    user_data_dir = ROOT_DIR / "data" / "playwright-profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            viewport={"width": 1366, "height": 900},
        )
        for index, url in enumerate(LOGIN_URLS):
            page = context.pages[0] if index == 0 and context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)

        while any(not page.is_closed() for page in context.pages):
            time.sleep(1)

        context.close()


if __name__ == "__main__":
    main()
