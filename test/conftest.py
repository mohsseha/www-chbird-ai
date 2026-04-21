"""Shared fixtures for the chbird.ai live-site test suite."""
from __future__ import annotations

import os
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


BASE_URL = os.environ.get("BASE_URL", "https://chbird.ai").rstrip("/")
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
HTTP_TIMEOUT = int(os.environ.get("HTTP_TIMEOUT", "15"))
PAGE_LOAD_TIMEOUT = int(os.environ.get("PAGE_LOAD_TIMEOUT", "30"))

# The pages that must exist on the live site. Source of truth: *.html at repo root.
PAGES = [
    "/",
    "/index.html",
    "/team.html",
    "/PM.html",
    "/MCP.html",
    "/compliance.html",
    "/legal.html",
    "/blog.html",
    "/public/devin.html",
]

# Breakpoints we check responsive rendering at.
VIEWPORTS = [
    ("desktop", 1440, 900),
    ("tablet", 768, 1024),
    ("mobile", 375, 812),
]


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Override BASE_URL (defaults to env BASE_URL or https://chbird.ai).",
    )


@pytest.fixture(scope="session")
def base_url(request) -> str:
    cli = request.config.getoption("--base-url")
    return (cli or BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def http() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "chbird-live-tests/1.0 (+selenium)"})
    return s


def _make_driver() -> webdriver.Chrome:
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1440,900")
    # Capture browser console logs so tests can assert on them.
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    # Selenium Manager resolves the driver automatically.
    driver = webdriver.Chrome(service=Service(), options=opts)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(0)
    return driver


@pytest.fixture(scope="session")
def driver():
    """Session-scoped driver; one Chrome for the whole run."""
    d = _make_driver()
    yield d
    d.quit()


@pytest.fixture
def fresh_driver():
    """Per-test driver when isolation from prior state is needed."""
    d = _make_driver()
    yield d
    d.quit()


@pytest.fixture(params=PAGES)
def page_path(request) -> str:
    return request.param


@pytest.fixture(params=VIEWPORTS, ids=lambda v: v[0])
def viewport(request):
    return request.param
