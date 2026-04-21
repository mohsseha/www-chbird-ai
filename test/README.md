# chbird.ai End-to-End Test Suite

Selenium-based tests that run **against the live deployed site** at https://chbird.ai.
These tests verify the production GitHub Pages deployment is not broken.

## What this suite covers

1. **Availability & HTTP** — every page returns 200, serves `text/html`, has an HTTPS cert.
2. **Navigation** — every `<a>` in the header/footer/cards points somewhere reachable; no dead internal links.
3. **Content integrity** — key elements present on each page (hero text, product cards, team photos, etc.).
4. **Assets** — images load (no 404s, non-zero naturalWidth), CSS loads, favicon resolves.
5. **Rendering** — no JS console errors, no horizontal scrollbar at 1440/768/375 widths.
6. **Accessibility smoke** — every `<img>` has `alt`, there is exactly one `<h1>`, page `<title>` is non-empty.
7. **SEO/meta** — `sitemap.xml`, `robots.txt`, and `CNAME` resolve correctly.

## Install

```bash
cd test
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Selenium Manager (built into Selenium 4.10+) downloads matching Chromedriver automatically
on first run — no manual driver install needed. Chrome (or Chromium) must exist on PATH.

## Run

```bash
# full suite, headless, against production
pytest -v

# run against a staging URL
BASE_URL=https://staging.chbird.ai pytest -v

# run visible browser (for debugging)
HEADLESS=0 pytest -v test_rendering.py

# run a single module
pytest -v test_availability.py
```

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `BASE_URL` | `https://chbird.ai` | Site under test (no trailing slash) |
| `HEADLESS` | `1` | `0` to show browser window |
| `HTTP_TIMEOUT` | `15` | Per-request timeout, seconds |
| `PAGE_LOAD_TIMEOUT` | `30` | Selenium page load timeout |

## CI

Exit code is non-zero on any failure. Designed to be wired to a scheduled GitHub Action
(or the existing Sparc cron) as a production canary.
