<div id="top"></div>

# 🕸️ Web Scraper & Data Collection Tool

A production-ready, browser-first web app to scrape static or dynamic web pages, extract tables or structured content via CSS selectors, paginate across pages, and export clean datasets in CSV, Excel (.xlsx), JSON, or TXT — all delivered as a direct download. Built with a pragmatic, extensible architecture using FastAPI, BeautifulSoup, Pandas, and optional Playwright + Celery.

<div align="center">
  <img src="assets/banner.svg" alt="Web Scraper banner" width="820"/>
</div>

<p align="left">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white" />
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img alt="Uvicorn" src="https://img.shields.io/badge/Uvicorn-000000?logo=uvicorn&logoColor=white" />
  <img alt="Requests" src="https://img.shields.io/badge/Requests-2D6DB6?logo=python&logoColor=white" />
  <img alt="BeautifulSoup" src="https://img.shields.io/badge/BeautifulSoup-4B8BBE?logo=python&logoColor=white" />
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white" />
  <img alt="openpyxl" src="https://img.shields.io/badge/openpyxl-4B8BBE?logo=python&logoColor=white" />
  <img alt="Playwright" src="https://img.shields.io/badge/Playwright-45BA63?logo=playwright&logoColor=white" />
  <img alt="Celery" src="https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white" />
  <img alt="Redis" src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" />
  <img alt="Bootstrap" src="https://img.shields.io/badge/Bootstrap-7952B3?logo=bootstrap&logoColor=white" />
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg" />
</p>

---

<h2 id="toc">🧭 Table of Contents</h2>

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [API and Parameters](#api)
- [Extraction & Export Details](#extraction-export)
- [Getting Started](#getting-started)
- [Docker & Optional Async](#docker-async)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [Performance Tips](#performance-tips)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

<h2 id="overview">🗺️ Overview</h2>

This application lets users input:
- a target URL,
- an optional CSS selector,
- an output format,
- optional dynamic rendering and pagination controls,

then returns a clean dataset as a file download. For pages with multiple HTML tables, Excel exports contain one worksheet per table. For non-table selectors, the app returns structured rows with useful fields (e.g., tag, text, absolute href/src, attributes).

[Back to top](#top)

---

<h2 id="architecture">🏗️ Architecture</h2>

- Presentation: Bootstrap form submits `multipart/form-data` to `/scrape`, and receives a streamed file.
- API: FastAPI routes (`/`, `/scrape`) validate inputs and orchestrate scraping + export.
- Scraping: `requests` (static) or `playwright` (dynamic) → `BeautifulSoup` for parsing → Pandas DataFrame(s).
- Export: CSV/JSON/TXT; Excel uses multi-sheet when multiple tables exist.
- Delivery: StreamingResponse sets correct MIME type and Content-Disposition.
- Optional async: Celery workers with Redis broker/result backend to offload heavy scrapes.

![Image](static/image.png)

[Back to top](#top)

---

<h2 id="data-flow">🔄 Data Flow (sequence)</h2>

```mermaid
flowchart LR
  U[Browser Form]
  A[FastAPI /scrape]
  S[HTML Parsing with BeautifulSoup]
  P[Pandas DataFrames]
  R[StreamingResponse]
  D[Download]

  U -->|POST form-data| A
  A -->|requests or Playwright| S
  S -->|tables or rows| P
  P -->|to_csv / to_json / to_excel| R
  R -->|attachment| D
```

[Back to top](#top)

---

<h2 id="api">🔌 API and Parameters</h2>

- GET `/` → Renders the form UI.
- POST `/scrape` → Accepts `multipart/form-data` and returns a streamed file.

Form fields:
- url (string, required): Must start with http:// or https://
- selector (string, optional): CSS selector to target elements/tables
- format (string, required): one of csv | xlsx | json | txt
- dynamic (bool, optional): "on"/"true"/"1" to enable Playwright
- wait_selector (string, optional): CSS selector Playwright should wait for
- wait_ms (int, optional): Additional wait in milliseconds
- page_param (string, optional): Query parameter name for page iteration (e.g., "page")
- page_start (int, optional): Start page index
- page_end (int, optional): End page index (inclusive)
- next_selector (string, optional): CSS selector for a “Next” link/button to follow
- max_pages (int, optional): Safety cap for next-link pagination
- delay_ms (int, optional): Delay between paginated requests

Response:
- 200 OK: Streaming file with headers:
  - Content-Type: text/csv | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | application/json | text/plain
  - Content-Disposition: attachment; filename=scraped.<ext>
- 400/500: HTML error message with brief diagnostics.

Curl example:
```bash
curl -X POST http://127.0.0.1:8000/scrape \
  -F "url=https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)" \
  -F "selector=table.wikitable" \
  -F "format=xlsx"
```

[Back to top](#top)

---

<h2 id="extraction-export">🧩 Extraction & Export Details</h2>

Tables:
- If the page or selector yields HTML tables, they are parsed into Pandas DataFrames.
- Excel export: multiple tables → multiple sheets (table_1, table_2, ...).

Non-table elements:
- When the selector targets non-table elements, rows include structured fields like:
  - tag, text, href (absolute if present), src (absolute if present), attributes (flattened/selected)
- Output renders cleanly across formats (CSV/JSON/TXT).

Dynamic rendering (optional):
- Enable when the page relies on JavaScript to populate content.
- Playwright launches headless Chromium, optionally:
  - waits for `wait_selector`
  - waits an additional `wait_ms` for stability
- Trade-offs: higher resource cost and latency vs. better completeness of content.

Pagination:
- Query parameter iteration: appends/replaces `?{page_param}={N}` for page_start..page_end.
- Next-link navigation: follows the anchor found by `next_selector` until not found or `max_pages` reached.
- Combine with `delay_ms` to be polite and avoid rate limits.

[Back to top](#top)

---

<h2 id="getting-started">🚀 Getting Started (Local)</h2>

Requirements:
- Python 3.11+
- Optional (dynamic pages): Playwright Chromium

Install and run:
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open <http://127.0.0.1:8000> and submit the form.

Playwright setup (optional, for dynamic pages):
```bash
python -m playwright install chromium
```

[Back to top](#top)

---

<h2 id="docker-async">🐳 Docker & Optional Async</h2>

Run with Docker:
```bash
docker-compose up --build
```
Web: <http://127.0.0.1:8000>

Optional Celery worker:
```bash
docker-compose run --rm worker
```

Notes:
- Async mode is optional; the standard path streams results immediately.
- For very large, long-running scrapes, consider enabling Celery + Redis and extending `/status` and `/result` endpoints.

[Back to top](#top)

---

<h2 id="project-structure">📂 Project Structure</h2>

```text
app/
  main.py        # FastAPI app and static mount
  routes.py      # Endpoints: /, /scrape (+ placeholders for async status)
  utils.py       # Scraping logic and file generation
  models.py      # Pydantic models (reserved for future)
templates/
  index.html     # Bootstrap form UI
static/
  css/style.css  # Custom light theme
  js/app.js      # Minimal JS (if needed)
tests/           # Basic tests
assets/
  banner.svg     # README/branding asset
```

[Back to top](#top)

---

<h2 id="usage-examples">🧑‍🏫 Usage Examples</h2>

1) Extract a Wikipedia table to CSV
- URL: A “List of …” page with tables
- Selector: `table.wikitable`
- Format: CSV

2) Extract article paragraphs to TXT
- URL: Any article
- Selector: `article p`
- Format: TXT

3) Dynamic content list to JSON with wait
- Enable “Dynamic rendering”
- Wait selector: `.list, #content, table` (whichever fits)
- Format: JSON

4) Paginate via query param to XLSX
- page_param: `page`
- page_start: 1, page_end: 5
- Selector: `table`
- Format: XLSX (will group multiple tables/pages)

[Back to top](#top)

---

<h2 id="performance-tips">⚙️ Performance Tips</h2>

- Provide specific CSS selectors (e.g., `table.data`, `.product-list > .item`) to reduce parsing overhead.
- Prefer `requests` unless the site is JS-heavy — toggle Playwright only when necessary.
- Use `page_end` or `max_pages` to prevent deep crawls.
- Add `delay_ms` for throttling to avoid bans or rate limits.
- Consider offloading heavy jobs to Celery workers in production.

[Back to top](#top)

---

<h2 id="security-notes">🔒 Security Notes</h2>

- Only http/https URLs are accepted.
- Respect robots.txt, site ToS, and legal constraints for scraping.
- Consider production hardening:
  - Rate limiting, timeouts, and retries policies
  - CSP and security headers
  - Input validation and URL allowlist per your org policy
  - Network egress rules for scraper containers

[Back to top](#top)

---

<h2 id="troubleshooting">🧩 Troubleshooting</h2>

- Empty CSV/Excel
  - Enable dynamic rendering and provide a `wait_selector` (e.g., `table`, `#content`).
  - Some sites block bots — adjust User-Agent or add `delay_ms`.
- No download
  - Ensure a format is selected and URL starts with http/https.
- Playwright errors
  - Install Chromium: `python -m playwright install chromium`

[Back to top](#top)

---

<h2 id="roadmap">🗺️ Roadmap (suggested)</h2>

- Add configurable headers, proxies, and per-site profiles.
- Enrich non-table extraction with configurable attribute whitelists.
- Add auth patterns (cookies/session/headers) for private data (where allowed).
- Production-grade Celery integration with persistent storage for results.
- Advanced pagination heuristics (auto-detect next links).

[Back to top](#top)

---

<h2 id="contributing">🤝 Contributing</h2>

- Open issues and PRs are welcome. Please:
  - Keep changes focused and tested.
  - Describe the behavior clearly and link any relevant pages for reproducibility.

[Back to top](#top)

---

<h2 id="license">📜 License</h2>

MIT © 2025 Youssef Chlih

[Back to top](#top)
