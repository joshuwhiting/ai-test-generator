import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page

from pages.base_page import accept_cookies_when_shown

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # The site blocks Playwright's bundled Chromium ("Access Denied"); use the installed Google Chrome
    return {
        **browser_type_launch_args,
        "channel": "chrome",
        "args": ["--disable-blink-features=AutomationControlled"],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, browser: Browser):
    # Headless Chrome reports "HeadlessChrome" in its user agent, which the site also blocks
    chrome_major = browser.version.split(".")[0]
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36"
        ),
    }


@pytest.fixture(autouse=True)
def cookie_banner(page: Page) -> None:
    accept_cookies_when_shown(page)


@pytest.fixture
def start_url() -> str:
    url = os.getenv("URL")
    if not url:
        pytest.fail("URL is not set. Add it to the .env file, e.g. URL=https://www.fourseasons.com/find_a_hotel_or_resort/")
    return url
