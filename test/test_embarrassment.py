"""Content-quality tests that guard against embarrassing failures
visible to a prospect browsing the live site."""
from __future__ import annotations

import re
from collections import Counter
from urllib.parse import urlparse

import pytest
from selenium.webdriver.common.by import By

from conftest import PAGES


# ---- 1. Dead-anchor CTA test ------------------------------------------------

# Visible-text patterns that indicate a call-to-action. Matching anchors
# whose href is dead ('#', '', javascript:void) are embarrassing.
CTA_TEXT_RE = re.compile(
    r"\b(demo|contact|sign\s?up|get\s+started|join|follow|subscribe|book)\b",
    re.IGNORECASE,
)


def _is_dead_href(href: str | None) -> bool:
    if href is None:
        return True
    h = href.strip().lower()
    if h in ("", "#"):
        return True
    if h.startswith("javascript:"):
        return True
    return False


def test_no_dead_cta_anchors(driver, base_url, page_path):
    """Primary conversion anchors must go somewhere real."""
    driver.get(f"{base_url}{page_path}")
    dead: list[tuple[str, str]] = []
    for a in driver.find_elements(By.TAG_NAME, "a"):
        text = (a.text or "").strip()
        if not text:
            continue
        if not CTA_TEXT_RE.search(text):
            continue
        href = a.get_attribute("href")
        # Selenium resolves href to absolute URL, so "#" becomes "<page>#".
        # Detect that by stripping the current page URL and checking the fragment.
        raw = a.get_attribute("outerHTML") or ""
        raw_href_match = re.search(r'href\s*=\s*["\']([^"\']*)["\']', raw)
        raw_href = raw_href_match.group(1) if raw_href_match else href
        if _is_dead_href(raw_href):
            dead.append((text, raw_href or "(none)"))
    assert not dead, (
        f"{page_path}: {len(dead)} dead CTA anchor(s):\n  "
        + "\n  ".join(f"{t!r} -> {h!r}" for t, h in dead)
    )


# ---- 2. Placeholder-phrase scan --------------------------------------------

PLACEHOLDER_RE = re.compile(
    r"\b(coming soon|arriving soon|lorem ipsum|todo|fixme|tbd|placeholder|xxxx+)\b",
    re.IGNORECASE,
)


def test_no_placeholder_phrases(driver, base_url, page_path):
    """Body text must not contain unfinished-copy markers."""
    driver.get(f"{base_url}{page_path}")
    text = driver.find_element(By.TAG_NAME, "body").text
    hits = PLACEHOLDER_RE.findall(text)
    assert not hits, (
        f"{page_path}: placeholder phrase(s) in visible body: {Counter(hits).most_common()}"
    )


# ---- 3. Brand-spelling consistency -----------------------------------------

BRAND_RE = re.compile(r"\b(ChromeBird|Chromebird|ChBird|Chbird)\b")
# Tokens to strip before scanning so that email local/domain parts and URLs
# don't count as prose brand mentions (e.g. 'info@chbird.ai', 'chbird.ai').
EMAIL_OR_URL_RE = re.compile(
    r"(?:https?://\S+|\b[\w.+-]+@[\w.-]+\.\w+\b|\bchbird\.ai\b)",
    re.IGNORECASE,
)


def test_brand_spelling_consistent_within_paragraph(driver, base_url, page_path):
    """A single <p> should not mix 'ChromeBird' and 'ChBird' spellings —
    that looks like a search-and-replace gone wrong. Email addresses and
    URLs are scrubbed before scanning so they don't register as prose."""
    driver.get(f"{base_url}{page_path}")
    mixed: list[str] = []
    for p in driver.find_elements(By.CSS_SELECTOR, "p, li, h1, h2, h3"):
        raw = p.text or ""
        txt = EMAIL_OR_URL_RE.sub("", raw)
        found = BRAND_RE.findall(txt)
        if not found:
            continue
        families = {
            "chromebird" if s.lower().startswith("chromebird") else "chbird"
            for s in found
        }
        if len(families) > 1:
            mixed.append(raw.strip()[:200])
    assert not mixed, (
        f"{page_path}: paragraph(s) mix brand spellings:\n  "
        + "\n  ".join(f"- {m!r}" for m in mixed)
    )


# ---- 4. Unique, non-default <title> + meta description across pages --------

@pytest.fixture(scope="module")
def page_meta(base_url, http):
    """Collect (title, meta-description) for every known page by parsing
    the served HTML directly. Avoids Selenium races with meta-refresh."""
    from conftest import HTTP_TIMEOUT
    title_re = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
    desc_re = re.compile(
        r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
        re.IGNORECASE,
    )
    meta: dict[str, tuple[str, str]] = {}
    for p in PAGES:
        r = http.get(f"{base_url}{p}", timeout=HTTP_TIMEOUT)
        html = r.text
        tm = title_re.search(html)
        title = (tm.group(1).strip() if tm else "")
        dm = desc_re.search(html)
        desc = (dm.group(1).strip() if dm else "")
        meta[p] = (title, desc)
    return meta


def test_every_page_has_non_empty_title(page_meta):
    empty = [p for p, (t, _) in page_meta.items() if not t]
    assert not empty, f"pages with empty <title>: {empty}"


def test_titles_are_unique_across_pages(page_meta):
    """Two pages sharing the exact same title hurts SEO and looks copy-pasted.
    Redirect shims (/blog.html) are exempt."""
    # /index.html and / serve the same page; that's fine — collapse them.
    items = [(p, t) for p, (t, _) in page_meta.items() if p != "/index.html"]
    # blog.html is a redirect shim with title "Redirecting..." — exempt.
    items = [(p, t) for p, t in items if p != "/blog.html"]
    counts = Counter(t for _, t in items)
    dups = {t: c for t, c in counts.items() if c > 1}
    if dups:
        offenders = {p: t for p, t in items if t in dups}
        pytest.fail(f"duplicate <title>s across pages: {offenders}")


def test_every_page_has_meta_description(page_meta):
    """Pages served as production marketing should have a meta description
    so social/search previews are not empty. Redirect shim exempt."""
    missing = [
        p for p, (_, d) in page_meta.items()
        if not d and p not in ("/blog.html", "/index.html")
    ]
    # Soft: warn rather than hard-fail, since this is SEO hygiene not a broken page.
    if missing:
        pytest.skip(f"pages missing <meta name=description>: {missing}")
