"""Every known page must be reachable and serve HTML."""
from __future__ import annotations

import pytest

from conftest import HTTP_TIMEOUT


def test_page_returns_200(http, base_url, page_path):
    r = http.get(f"{base_url}{page_path}", timeout=HTTP_TIMEOUT, allow_redirects=True)
    assert r.status_code == 200, f"{page_path} -> {r.status_code}"


def test_page_is_html(http, base_url, page_path):
    r = http.get(f"{base_url}{page_path}", timeout=HTTP_TIMEOUT, allow_redirects=True)
    ct = r.headers.get("content-type", "")
    assert "text/html" in ct.lower(), f"{page_path} content-type is {ct!r}"


def test_http_redirects_to_https(http, base_url):
    # GitHub Pages should upgrade http:// -> https://
    if not base_url.startswith("https://"):
        pytest.skip("base_url is not https; skipping redirect check")
    http_url = "http://" + base_url.removeprefix("https://")
    r = http.get(http_url + "/", timeout=HTTP_TIMEOUT, allow_redirects=True)
    assert r.url.startswith("https://"), f"no HTTPS upgrade: final URL {r.url}"
    assert r.status_code == 200


def test_robots_txt(http, base_url):
    r = http.get(f"{base_url}/robots.txt", timeout=HTTP_TIMEOUT)
    assert r.status_code == 200, f"robots.txt -> {r.status_code}"
    assert "user-agent" in r.text.lower()


def test_sitemap_xml(http, base_url):
    r = http.get(f"{base_url}/sitemap.xml", timeout=HTTP_TIMEOUT)
    assert r.status_code == 200, f"sitemap.xml -> {r.status_code}"
    assert "<urlset" in r.text or "<sitemapindex" in r.text


def test_favicon(http, base_url):
    r = http.get(f"{base_url}/favicon.ico", timeout=HTTP_TIMEOUT)
    assert r.status_code == 200, f"favicon -> {r.status_code}"
    assert int(r.headers.get("content-length", "1")) > 0


def test_404_page_is_not_served_for_known_routes(http, base_url):
    # Defensive: ensure GitHub Pages isn't silently 404-ing into a 200 shell.
    r = http.get(f"{base_url}/definitely-not-a-real-page-xyz.html", timeout=HTTP_TIMEOUT)
    assert r.status_code == 404, (
        f"expected 404 for unknown path, got {r.status_code} — "
        "site may be serving a soft-404 which would mask real breakages"
    )
