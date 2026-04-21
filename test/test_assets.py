"""Every <img> must actually load; every <link rel=stylesheet> must resolve."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

import pytest
import requests
from selenium.webdriver.common.by import By

from conftest import HTTP_TIMEOUT


def test_all_images_loaded(driver, base_url, page_path):
    driver.get(f"{base_url}{page_path}")
    imgs = driver.find_elements(By.TAG_NAME, "img")
    failed: list[str] = []
    for img in imgs:
        # naturalWidth == 0 means the image failed to load (404, CORS, bad src).
        nw = driver.execute_script("return arguments[0].naturalWidth;", img)
        complete = driver.execute_script("return arguments[0].complete;", img)
        src = img.get_attribute("src") or "(no src)"
        if not complete or not nw:
            failed.append(f"{src} (naturalWidth={nw}, complete={complete})")
    assert not failed, (
        f"{page_path}: {len(failed)} image(s) failed to load:\n  "
        + "\n  ".join(failed)
    )


def test_page_is_styled(driver, base_url, page_path, http):
    """Page must either link a stylesheet or embed inline CSS — otherwise it renders with
    browser defaults (usually an embarrassment)."""
    driver.get(f"{base_url}{page_path}")
    links = driver.find_elements(By.CSS_SELECTOR, 'link[rel="stylesheet"]')
    inline = driver.find_elements(By.TAG_NAME, "style")
    inline_chars = sum(
        len(driver.execute_script("return arguments[0].textContent;", s) or "")
        for s in inline
    )
    assert links or inline_chars > 200, (
        f"{page_path} has no external stylesheets and <200 chars of inline CSS — "
        "likely rendering unstyled"
    )
    broken: list[tuple[str, int]] = []
    for link in links:
        href = link.get_attribute("href")
        if not href:
            continue
        r = http.get(href, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            broken.append((href, r.status_code))
    assert not broken, f"{page_path}: broken stylesheets: {broken}"


def test_main_stylesheet_served(http, base_url):
    """style.css at repo root is the main stylesheet per Jekyll layout."""
    r = http.get(f"{base_url}/style.css", timeout=HTTP_TIMEOUT)
    assert r.status_code == 200, f"style.css -> {r.status_code}"
    assert len(r.content) > 500, "style.css suspiciously small"
    assert "text/css" in r.headers.get("content-type", "").lower()


def test_all_scripts_load(driver, base_url, page_path, http):
    driver.get(f"{base_url}{page_path}")
    scripts = driver.find_elements(By.CSS_SELECTOR, "script[src]")
    host = urlparse(base_url).netloc
    broken: list[tuple[str, int]] = []
    for s in scripts:
        src = s.get_attribute("src")
        if not src:
            continue
        # Only check same-origin scripts; third-party CDNs can rate-limit HEAD.
        if urlparse(src).netloc and urlparse(src).netloc != host:
            continue
        r = http.get(src, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            broken.append((src, r.status_code))
    assert not broken, f"{page_path}: broken scripts: {broken}"


def test_all_images_have_alt(driver, base_url, page_path):
    driver.get(f"{base_url}{page_path}")
    imgs = driver.find_elements(By.TAG_NAME, "img")
    missing = [
        (img.get_attribute("src") or "(no src)")
        for img in imgs
        if img.get_attribute("alt") is None
    ]
    assert not missing, f"{page_path}: images missing alt attribute: {missing}"
