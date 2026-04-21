"""Rendering sanity: no JS console errors, no horizontal scroll at common widths."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By


# Console messages that match these substrings are ignored (benign noise).
CONSOLE_IGNORE = (
    "favicon.ico",                     # some browsers warn when favicon is absent
    "Failed to load resource: net::ERR_BLOCKED_BY_CLIENT",  # ad-blockers in dev
    "the server responded with a status of 0",
)

# Pages that are pure redirect shims — rendering/overflow/readyState checks
# don't apply because Selenium races the JS/meta redirect.
REDIRECT_PAGES = {"/blog.html"}


def _console_errors(driver) -> list[str]:
    logs = driver.get_log("browser")
    errs = []
    for entry in logs:
        if entry.get("level") != "SEVERE":
            continue
        msg = entry.get("message", "")
        if any(ig in msg for ig in CONSOLE_IGNORE):
            continue
        errs.append(msg)
    return errs


def test_no_severe_console_errors(fresh_driver, base_url, page_path):
    fresh_driver.get(f"{base_url}{page_path}")
    errs = _console_errors(fresh_driver)
    assert not errs, f"{page_path}: SEVERE console errors:\n  " + "\n  ".join(errs)


def test_no_horizontal_scrollbar(fresh_driver, base_url, page_path, viewport):
    if page_path in REDIRECT_PAGES:
        pytest.skip(f"{page_path} is a redirect shim")
    name, w, h = viewport
    fresh_driver.set_window_size(w, h)
    fresh_driver.get(f"{base_url}{page_path}")
    # A horizontal scrollbar appears when scrollWidth > clientWidth on documentElement.
    scroll_w, client_w = fresh_driver.execute_script(
        "return [document.documentElement.scrollWidth, document.documentElement.clientWidth];"
    )
    # Allow 2px slop for subpixel rounding.
    assert scroll_w <= client_w + 2, (
        f"{page_path} @ {name} ({w}x{h}): horizontal overflow "
        f"(scrollWidth={scroll_w}, clientWidth={client_w})"
    )


def test_body_has_visible_text(driver, base_url, page_path):
    driver.get(f"{base_url}{page_path}")
    text_len = driver.execute_script(
        "return (document.body.innerText || '').trim().length;"
    )
    assert text_len > 50, f"{page_path} has <50 chars of visible text ({text_len})"


def test_page_fully_loaded(driver, base_url, page_path):
    if page_path in REDIRECT_PAGES:
        pytest.skip(f"{page_path} is a redirect shim")
    driver.get(f"{base_url}{page_path}")
    ready = driver.execute_script("return document.readyState;")
    assert ready == "complete", f"{page_path} readyState={ready}"


def test_blog_redirects_to_substack(http, base_url):
    """blog.html is intentionally a meta-refresh/JS redirect to Substack.
    Verify the redirect target is still pointed at the right place."""
    from conftest import HTTP_TIMEOUT
    r = http.get(f"{base_url}/blog.html", timeout=HTTP_TIMEOUT)
    assert r.status_code == 200
    html = r.text
    assert "chromebird.substack.com" in html, (
        "blog.html no longer points at chromebird.substack.com — "
        "either the redirect was removed or the target changed"
    )


def test_no_jekyll_liquid_leaks(driver, base_url, page_path):
    """If Jekyll build broke, you can see raw `{{ ... }}` or `{% ... %}` in output."""
    driver.get(f"{base_url}{page_path}")
    html = driver.page_source
    # These are Liquid delimiters that should never appear in rendered output.
    assert "{% " not in html, f"{page_path}: unrendered Liquid tag leaked"
    assert " %}" not in html, f"{page_path}: unrendered Liquid tag leaked"
    # {{ ... }} is trickier (could be literal CSS/JS), check only Jekyll-style vars.
    for token in ("{{ page.", "{{ site.", "{{ content"):
        assert token not in html, f"{page_path}: unrendered Liquid variable: {token}"
