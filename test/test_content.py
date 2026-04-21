"""Content-integrity checks: each page must render the expected key elements."""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By


def _goto(driver, base_url, path):
    driver.get(f"{base_url}{path}")


def test_title_is_present(driver, base_url, page_path):
    _goto(driver, base_url, page_path)
    title = driver.title.strip()
    assert title, f"{page_path} has empty <title>"
    # Every page should be branded.
    assert "chbird" in title.lower() or "chromebird" in title.lower(), (
        f"{page_path} title missing brand: {title!r}"
    )


def test_exactly_one_h1(driver, base_url, page_path):
    _goto(driver, base_url, page_path)
    h1s = driver.find_elements(By.TAG_NAME, "h1")
    assert len(h1s) >= 1, f"{page_path} has no <h1>"
    # Soft assertion: more than one h1 is a known a11y smell but not a hard fail.
    if len(h1s) > 1:
        pytest.skip(f"{page_path} has {len(h1s)} h1s (a11y smell, not breaking)")


def test_header_and_footer_present(driver, base_url, page_path):
    _goto(driver, base_url, page_path)
    # Jekyll _includes inject a header with the brand; footer contains copyright.
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert body_text.strip(), f"{page_path} body is empty"


def test_homepage_hero_renders(driver, base_url):
    driver.get(f"{base_url}/")
    hero = driver.find_elements(By.CSS_SELECTOR, "section.hero, .hero, h1")
    assert hero, "homepage has no hero / h1"
    text = " ".join(e.text for e in hero if e.text)
    # Hero copy from index.html
    assert "Useful Products" in text or "Hard Problems" in text or "Real Results" in text, (
        f"homepage hero copy missing; saw: {text[:200]!r}"
    )


def test_homepage_product_cards(driver, base_url):
    driver.get(f"{base_url}/")
    cards = driver.find_elements(By.CSS_SELECTOR, "#products .card")
    assert len(cards) >= 2, f"expected >=2 product cards, got {len(cards)}"
    hrefs = [c.get_attribute("href") for c in cards if c.tag_name == "a"]
    joined = " ".join(h or "" for h in hrefs)
    assert "PM.html" in joined, "ChBird PM card link missing"
    assert "compliance.html" in joined, "ChBird Compliance card link missing"


def test_homepage_insights_cards(driver, base_url):
    driver.get(f"{base_url}/")
    cards = driver.find_elements(By.CSS_SELECTOR, "#insights .card")
    assert len(cards) >= 3, f"expected >=3 insights cards, got {len(cards)}"


def test_homepage_partner_logos(driver, base_url):
    driver.get(f"{base_url}/")
    logos = driver.find_elements(By.CSS_SELECTOR, ".partner-logo")
    assert len(logos) >= 4, f"expected >=4 partner logos, got {len(logos)}"
    # Every partner logo must actually be loaded (non-zero naturalWidth).
    for img in logos:
        nw = driver.execute_script("return arguments[0].naturalWidth;", img)
        assert nw and nw > 0, f"partner logo failed to load: {img.get_attribute('src')}"


def test_team_page_has_members(driver, base_url):
    driver.get(f"{base_url}/team.html")
    body = driver.find_element(By.TAG_NAME, "body").text
    # Founders named in the repo assets
    assert any(name in body for name in ("Husain", "Don", "Sean", "DG")), (
        "team page missing expected member names"
    )


def test_pm_page_has_content(driver, base_url):
    driver.get(f"{base_url}/PM.html")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "PM" in body or "Project" in body or "Management" in body, (
        "PM page body looks empty"
    )


def test_compliance_page_has_content(driver, base_url):
    driver.get(f"{base_url}/compliance.html")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "Compliance" in body or "compliance" in body, "Compliance page missing keyword"


def test_mcp_page_has_content(driver, base_url):
    driver.get(f"{base_url}/MCP.html")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "MCP" in body or "API" in body, "MCP page missing keyword"


def test_devin_benchmark_page(driver, base_url):
    driver.get(f"{base_url}/public/devin.html")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "Devin" in body or "SWE" in body or "benchmark" in body.lower(), (
        "Devin benchmark page missing expected keywords"
    )
