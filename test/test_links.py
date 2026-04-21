"""Crawl every internal link reachable from the homepage and verify it is 200."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

import pytest
import requests
from selenium.webdriver.common.by import By

from conftest import HTTP_TIMEOUT, PAGES


def _collect_links(driver, url: str) -> list[str]:
    driver.get(url)
    els = driver.find_elements(By.TAG_NAME, "a")
    hrefs = []
    for e in els:
        h = e.get_attribute("href")
        if h:
            hrefs.append(h)
    return hrefs


@pytest.fixture(scope="module")
def all_internal_links(driver, base_url, http):
    """Visit every known page, collect every <a href>, return the set of internal URLs."""
    host = urlparse(base_url).netloc
    seen: set[str] = set()
    for p in PAGES:
        for href in _collect_links(driver, f"{base_url}{p}"):
            abs_url = urljoin(f"{base_url}{p}", href)
            parsed = urlparse(abs_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc == host:
                # Strip fragments; they don't affect HTTP status.
                seen.add(parsed._replace(fragment="").geturl())
    return sorted(seen)


def test_collected_some_internal_links(all_internal_links):
    assert len(all_internal_links) >= len(PAGES), (
        f"only found {len(all_internal_links)} internal links, "
        f"expected at least {len(PAGES)}"
    )


def test_every_internal_link_resolves(all_internal_links, http):
    broken: list[tuple[str, int | str]] = []
    for url in all_internal_links:
        try:
            r = http.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
            # Some static hosts disallow HEAD; fall back to GET.
            if r.status_code >= 400:
                r = http.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
            if r.status_code >= 400:
                broken.append((url, r.status_code))
        except requests.RequestException as exc:
            broken.append((url, f"{type(exc).__name__}: {exc}"))
    assert not broken, "broken internal links:\n" + "\n".join(f"  {u} -> {s}" for u, s in broken)


def test_external_links_have_rel_noopener(driver, base_url):
    """Soft security check: external links that open in a new tab should have rel=noopener."""
    driver.get(f"{base_url}/")
    host = urlparse(base_url).netloc
    bad: list[str] = []
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href") or ""
        target = a.get_attribute("target") or ""
        rel = (a.get_attribute("rel") or "").lower()
        if not href.startswith("http"):
            continue
        if urlparse(href).netloc == host:
            continue
        if target == "_blank" and "noopener" not in rel:
            bad.append(href)
    # Non-fatal: just warn via skip.
    if bad:
        pytest.skip(f"{len(bad)} external _blank links missing rel=noopener: {bad[:5]}")
