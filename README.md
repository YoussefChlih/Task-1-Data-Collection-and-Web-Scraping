<div align="center">

<img src="assets/banner.svg" alt="Web Scraper banner" width="820"/>

<p>
	<a href="https://github.com/YoussefChlih/Task-1-Data-Collection-and-Web-Scraping/actions"><img alt="CI" src="https://img.shields.io/badge/CI-Lint%20%7C%20Tests-blue"/></a>
	<img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white"/>
	<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async%20API-009688?logo=fastapi&logoColor=white"/>
	<img alt="License" src="https://img.shields.io/badge/License-MIT-green"/>
</p>

</div>

# Web Scraper · Data Collection & Export

Web application that fetches a URL, optionally applies a CSS selector, and exports the extracted data as CSV, Excel (.xlsx), JSON, or TXT. Supports multi-table pages, dynamic rendering (Playwright), and pagination.

## Features

- Direct download from the browser (no job ID required)
- Tables detection and multi-sheet Excel export
- Structured extraction for non-table elements (tag, text, href/src absolute, attributes)
- Optional dynamic rendering (Playwright) for JS-heavy pages
- Pagination support:
	- Query parameter iteration (page=X)
	- Next-link navigation via CSS selector
- Clean, accessible light theme UI (Bootstrap + custom CSS)

## Stack

- FastAPI (web/API), Uvicorn (ASGI)
- Requests (HTTP), BeautifulSoup + lxml (HTML parsing)
- Pandas + openpyxl (DataFrames and Excel)
- Optional: Playwright (dynamic rendering)
- Optional: Celery + Redis (async jobs)

## Architecture (overview)

- Presentation: Bootstrap form posts to `/scrape` (form-data), server streams downloadable file.
- Application: FastAPI endpoints, simple validation, streaming responses with correct MIME types.
- Scraping: `requests` or `playwright` → `BeautifulSoup` → DataFrames (tables dict or structured rows).
- Export: CSV/JSON/TXT (labeled, single sheet), Excel multi-sheet if multiple tables.
- Optional async: Celery worker to offload heavy jobs; Redis as broker/result backend.

```mermaid
flowchart LR
	U[Browser Form] -->|POST form-data| A[FastAPI /scrape]
	A -->|requests / playwright| S[HTML Parsing (BeautifulSoup)]
	S -->|tables or rows| P[Pandas DataFrame(s)]
	P -->|to_csv/to_json/to_excel| R[StreamingResponse]
	R -->|attachment| D[Download]
```

## How it works

1) User enters URL, optional CSS selector, and selects output format.
2) Server fetches the page (requests or Playwright if enabled), parses HTML with BeautifulSoup.
3) If tables are detected → builds a dict of DataFrames; else builds a structured DataFrame of elements.
4) Exports to the chosen format and streams back with `Content-Disposition: attachment`.

## Libraries and why

- FastAPI: performant async API, type hints, clear routing.
- Uvicorn: ASGI server.
- Requests: robust HTTP client for static pages.
- BeautifulSoup + lxml: fast, reliable parsing and CSS selectors.
- Pandas: tabular transformations; `read_html` for tables.
- openpyxl: Excel writer.
- Playwright (optional): headless browser for JS-rendered content.
- Celery + Redis (optional): offload heavy scraping to workers.

## Getting started (local)

Requirements: Python 3.11+

```powershell
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 and submit the form.

Dynamic pages (optional): Install browsers for Playwright once

```powershell
python -m playwright install chromium
```

## Docker

```powershell
docker-compose up --build
```

Web: http://127.0.0.1:8000

## Optional: Celery worker

```powershell
docker-compose run --rm worker
```

## Project structure

```
app/
	main.py        # FastAPI app and routing
	routes.py      # Endpoints: /, /scrape
	utils.py       # Scraping and file generation
	models.py      # Pydantic models (if needed later)
templates/
	index.html     # Form UI
static/
	css/style.css  # Light theme styles
	js/app.js      # (minimal)
tests/           # Basic tests
assets/
	banner.svg     # README banner
```

## Security notes

- Only http/https URLs accepted.
- Consider adding rate-limiting and CSP headers in production.
- Respect robots.txt and site ToS when scraping.

## Troubleshooting

- Empty Excel or CSV:
	- Enable dynamic rendering and provide a wait selector (e.g., `table`, `#content`).
	- Some sites block bots → adjust User-Agent or delay.
- No download:
	- Ensure a format is selected and URL is http/https.
- Playwright errors:
	- Install Chromium (`python -m playwright install chromium`).

## License

MIT © 2025 Youssef Chlih
