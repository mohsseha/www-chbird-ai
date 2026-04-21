"""Lightweight security / best-practice checks on the live site."""
from __future__ import annotations

import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime, timezone

import pytest

from conftest import HTTP_TIMEOUT


def test_https_certificate_valid(base_url):
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        pytest.skip("base_url is not https")
    host = parsed.hostname
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=HTTP_TIMEOUT) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )
    days_left = (not_after - datetime.now(timezone.utc)).days
    assert days_left > 7, f"cert for {host} expires in {days_left} days"


def test_cname_matches_domain(http, base_url):
    """CNAME file at site root should match the host we're testing against."""
    r = http.get(f"{base_url}/CNAME", timeout=HTTP_TIMEOUT)
    if r.status_code == 404:
        pytest.skip("CNAME not exposed (may be stripped by host)")
    expected = urlparse(base_url).hostname
    actual = r.text.strip()
    assert actual == expected, f"CNAME={actual!r} but base_url host={expected!r}"


def test_no_source_maps_exposed(http, base_url):
    r = http.get(f"{base_url}/style.css.map", timeout=HTTP_TIMEOUT)
    # 404 is the desired outcome; GitHub Pages often serves a soft-404 HTML page,
    # so accept either 404 or non-JSON content.
    if r.status_code == 200:
        # Must not be actual source-map JSON.
        assert not r.text.lstrip().startswith("{"), "style.css.map source map is exposed"


def test_sensitive_files_not_exposed(http, base_url):
    for path in ("/_config.yml", "/Gemfile", "/Gemfile.lock", "/.git/config"):
        r = http.get(f"{base_url}{path}", timeout=HTTP_TIMEOUT)
        assert r.status_code in (404, 403), (
            f"{path} is publicly accessible (status {r.status_code}) — should be 404/403"
        )
