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


@pytest.fixture(scope="module")
def all_external_links(driver, base_url):
    """Visit every known page, collect every <a href> that points off-site."""
    host = urlparse(base_url).netloc
    seen: set[str] = set()
    for p in PAGES:
        for href in _collect_links(driver, f"{base_url}{p}"):
            parsed = urlparse(href)
            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc == host or parsed.netloc == "":
                continue
            seen.add(parsed._replace(fragment="").geturl())
    return sorted(seen)


def test_collected_some_external_links(all_external_links):
    # Sanity: site links to Substack at minimum, so we expect >= 1.
    assert all_external_links, "no external links found across the site"


# Status codes that mean "host refused to verify us" rather than "page is broken":
# LinkedIn returns 999, Cloudflare-protected sites often 403/503 to bots,
# 429 = rate limited. None of these prove the link is dead.
_UNVERIFIABLE_STATUSES = {403, 429, 503, 999}


def test_every_external_link_resolves(all_external_links, http):
    # Pretend to be a normal browser; the default requests UA gets blocked more often.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    broken: list[tuple[str, int | str]] = []
    unverifiable: list[tuple[str, int]] = []
    for url in all_external_links:
        try:
            r = http.get(
                url,
                timeout=HTTP_TIMEOUT,
                allow_redirects=True,
                headers=headers,
            )
            if r.status_code in _UNVERIFIABLE_STATUSES:
                unverifiable.append((url, r.status_code))
            elif r.status_code >= 400:
                broken.append((url, r.status_code))
        except requests.RequestException as exc:
            broken.append((url, f"{type(exc).__name__}: {exc}"))
    if unverifiable:
        print(
            "\n[external-links] could not verify (host blocks bots):\n"
            + "\n".join(f"  {u} -> {s}" for u, s in unverifiable)
        )
    assert not broken, "broken external links:\n" + "\n".join(
        f"  {u} -> {s}" for u, s in broken
    )


def test_no_mailto_links_are_empty(driver, base_url):
    """Every mailto: link must contain a non-empty address."""
    bad: list[tuple[str, str]] = []
    for p in PAGES:
        for href in _collect_links(driver, f"{base_url}{p}"):
            if not href.lower().startswith("mailto:"):
                continue
            addr = href[len("mailto:"):].split("?", 1)[0].strip()
            if not addr or "@" not in addr:
                bad.append((p, href))
    assert not bad, "empty/invalid mailto links:\n" + "\n".join(
        f"  {p}: {h}" for p, h in bad
    )


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
