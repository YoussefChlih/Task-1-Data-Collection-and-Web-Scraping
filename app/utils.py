import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from typing import Dict, List, Tuple, Union, Optional
from urllib.parse import urljoin
import os

def scrape_data(
    url: str,
    selector: Optional[str] = None,
    *,
    dynamic: bool = False,
    wait_selector: Optional[str] = None,
    wait_ms: Optional[int] = None,
    page_param: Optional[str] = None,
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
    next_selector: Optional[str] = None,
    max_pages: Optional[int] = None,
    delay_ms: Optional[int] = None,
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Fetch URL(s) and return structured data.
    Supports:
      - Dynamic rendering via Playwright when dynamic=True
      - Pagination via query param (page_param, page_start..page_end)
      - Pagination via next link CSS (next_selector, max_pages)
    Returns dict of DataFrames for multiple tables, or a single DataFrame otherwise.
    """

    def fetch_html(target_url: str) -> Tuple[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        }
        # Disable dynamic on Vercel serverless (no browser runtime)
        dynamic_allowed = dynamic and not os.getenv("VERCEL")
        if dynamic_allowed:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    page = context.new_page()
                    page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    if wait_selector:
                        try:
                            page.wait_for_selector(wait_selector, timeout=(wait_ms or 3000))
                        except Exception:
                            pass
                    elif wait_ms:
                        page.wait_for_timeout(wait_ms)
                    content = page.content()
                    final_url = page.url
                    context.close()
                    browser.close()
                    return content, final_url
            except Exception:
                # Fallback to static fetch
                pass
        resp = requests.get(target_url, timeout=20, headers=headers)
        resp.raise_for_status()
        return resp.text, resp.url

    def parse_html(html: str, base_url: str) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        soup = BeautifulSoup(html, 'lxml')
        
        def parse_tables_from(tags: List) -> List[pd.DataFrame]:
            dfs: List[pd.DataFrame] = []
            for t in tags:
                try:
                    sub = pd.read_html(str(t))
                    for d in sub:
                        d.columns = [str(c).strip() for c in d.columns]
                        dfs.append(d)
                except ValueError:
                    continue
            return dfs

        if selector:
            selected = soup.select(selector)
            if selected:
                tables = [el for el in selected if el.name == 'table' or el.find('table')]
                if tables:
                    dfs = parse_tables_from(tables)
                    if dfs:
                        return {f"table_{i+1}": df for i, df in enumerate(dfs)}
                rows = []
                for el in selected:
                    tag = el.name
                    text = el.get_text(" ", strip=True)
                    raw_href = el.get('href')
                    raw_src = el.get('src')
                    href = urljoin(base_url, raw_href) if raw_href else None
                    src = urljoin(base_url, raw_src) if raw_src else None
                    title = el.get('title')
                    aria = el.get('aria-label')
                    classes = " ".join(el.get('class', [])) if el.has_attr('class') else None
                    if any([text, href, src, title, aria, classes]):
                        rows.append({
                            'tag': tag,
                            'text': text,
                            'href': href,
                            'src': src,
                            'title': title,
                            'aria_label': aria,
                            'classes': classes,
                        })
                df = pd.DataFrame(rows)
                if df.empty:
                    df = pd.DataFrame([{"message": "No content matched the selector."}])
                return df

        page_tables = soup.find_all('table')
        dfs = parse_tables_from(page_tables)
        if dfs:
            return {f"table_{i+1}": df for i, df in enumerate(dfs)}

        candidates = soup.select('article, main, section, h1, h2, h3, h4, p, li, a')
        rows = []
        for el in candidates[:1000]:
            tag = el.name
            text = el.get_text(" ", strip=True)
            raw_href = el.get('href')
            raw_src = el.get('src')
            href = urljoin(base_url, raw_href) if raw_href else None
            src = urljoin(base_url, raw_src) if raw_src else None
            title = el.get('title')
            aria = el.get('aria-label')
            classes = " ".join(el.get('class', [])) if el.has_attr('class') else None
            if any([text, href, src, title, aria, classes]):
                rows.append({
                    'tag': tag,
                    'text': text,
                    'href': href,
                    'src': src,
                    'title': title,
                    'aria_label': aria,
                    'classes': classes,
                })
        df = pd.DataFrame(rows)
        if df.empty:
            body_text = soup.get_text(" ", strip=True)
            df = pd.DataFrame({'text': [body_text]})
        return df

    # Single page helper
    def scrape_single(target_url: str) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        html, final = fetch_html(target_url)
        return parse_html(html, final)

    # Pagination strategy 1: query param iteration
    if page_param and page_start is not None and page_end is not None:
        all_tables: Dict[str, pd.DataFrame] = {}
        all_rows: List[pd.DataFrame] = []
        for p in range(page_start, page_end + 1):
            connector = '&' if ('?' in url) else '?'
            page_url = f"{url}{connector}{page_param}={p}"
            data = scrape_single(page_url)
            if isinstance(data, dict):
                for name, df in data.items():
                    all_tables[f"p{p}_{name}"] = df
            else:
                d = data.copy()
                d.insert(0, 'page', p)
                all_rows.append(d)
            if delay_ms:
                try:
                    import time
                    time.sleep(delay_ms / 1000.0)
                except Exception:
                    pass
        if all_tables:
            return all_tables
        return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame([{"message": "No data"}])

    # Pagination strategy 2: next link selector
    if next_selector:
        visited = set()
        current_url = url
        count = 0
        all_tables: Dict[str, pd.DataFrame] = {}
        all_rows: List[pd.DataFrame] = []
        while current_url and (max_pages is None or count < max_pages):
            count += 1
            html, final = fetch_html(current_url)
            visited.add(final)
            parsed = parse_html(html, final)
            if isinstance(parsed, dict):
                for name, df in parsed.items():
                    all_tables[f"p{count}_{name}"] = df
            else:
                d = parsed.copy()
                d.insert(0, 'page', count)
                all_rows.append(d)
            # find next
            soup = BeautifulSoup(html, 'lxml')
            nxt = soup.select_one(next_selector)
            href = nxt.get('href') if nxt else None
            nxt_url = urljoin(final, href) if href else None
            if not nxt_url or nxt_url in visited:
                break
            current_url = nxt_url
            if delay_ms:
                try:
                    import time
                    time.sleep(delay_ms / 1000.0)
                except Exception:
                    pass
        if all_tables:
            return all_tables
        return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame([{"message": "No data"}])

    # Default: single page
    return scrape_single(url)

    # Helper to parse tables from a list of tags
    def parse_tables_from(tags: List) -> List[pd.DataFrame]:
        dfs: List[pd.DataFrame] = []
        for t in tags:
            try:
                sub = pd.read_html(str(t))
                for i, d in enumerate(sub):
                    # Normalize headers: if unnamed columns, keep as is; strip whitespace
                    d.columns = [str(c).strip() for c in d.columns]
                    dfs.append(d)
            except ValueError:
                # No tables parsed from this element
                continue
        return dfs

    # 1) If selector provided and targets tables, prioritize that
    if selector:
        selected = soup.select(selector)
        if selected:
            tables = [el for el in selected if el.name == 'table' or el.find('table')]
            if tables:
                dfs = parse_tables_from(tables)
                if dfs:
                    return {f"table_{i+1}": df for i, df in enumerate(dfs)}
            # Non-table elements: build structured rows
            rows = []
            for el in selected:
                tag = el.name
                text = el.get_text(" ", strip=True)
                raw_href = el.get('href')
                raw_src = el.get('src')
                href = urljoin(base_url, raw_href) if raw_href else None
                src = urljoin(base_url, raw_src) if raw_src else None
                title = el.get('title')
                aria = el.get('aria-label')
                classes = " ".join(el.get('class', [])) if el.has_attr('class') else None
                if any([text, href, src, title, aria, classes]):
                    rows.append({
                        'tag': tag,
                        'text': text,
                        'href': href,
                        'src': src,
                        'title': title,
                        'aria_label': aria,
                        'classes': classes,
                    })
            df = pd.DataFrame(rows)
            if df.empty:
                df = pd.DataFrame([{"message": "No content matched the selector."}])
            return df

    # 2) No selector or selector yielded no tables: try all tables on the page
    page_tables = soup.find_all('table')
    dfs = parse_tables_from(page_tables)
    if dfs:
        return {f"table_{i+1}": df for i, df in enumerate(dfs)}

    # 3) Fallback: collect common content elements
    candidates = soup.select('article, main, section, h1, h2, h3, h4, p, li, a')
    rows = []
    for el in candidates[:1000]:  # cap to avoid huge outputs
        tag = el.name
        text = el.get_text(" ", strip=True)
        raw_href = el.get('href')
        raw_src = el.get('src')
        href = urljoin(base_url, raw_href) if raw_href else None
        src = urljoin(base_url, raw_src) if raw_src else None
        title = el.get('title')
        aria = el.get('aria-label')
        classes = " ".join(el.get('class', [])) if el.has_attr('class') else None
        # Skip empty rows
        if any([text, href, src, title, aria, classes]):
            rows.append({
                'tag': tag,
                'text': text,
                'href': href,
                'src': src,
                'title': title,
                'aria_label': aria,
                'classes': classes,
            })
    df = pd.DataFrame(rows)
    if df.empty:
        # As a last resort, dump full text
        body_text = soup.get_text(" ", strip=True)
        df = pd.DataFrame({'text': [body_text]})
    return df

def generate_file(data: Union[pd.DataFrame, Dict[str, pd.DataFrame], List[pd.DataFrame]], format: str) -> bytes:
    fmt = format.lower().strip()

    # Normalize input into a dict for multi-table handling where applicable
    sheets: Optional[Dict[str, pd.DataFrame]] = None
    if isinstance(data, dict):
        sheets = data
    elif isinstance(data, list):
        sheets = {f"sheet_{i+1}": d for i, d in enumerate(data)}

    if fmt == 'xlsx':
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if sheets:
                for name, df in sheets.items():
                    safe = (name or 'Sheet')[:31]
                    to_write = df if not df.empty else pd.DataFrame([{"message": "No data"}])
                    to_write.to_excel(writer, index=False, sheet_name=safe)
            else:
                df = data  # type: ignore
                to_write = df if not getattr(df, 'empty', True) else pd.DataFrame([{"message": "No data"}])
                to_write.to_excel(writer, index=False, sheet_name='Sheet1')
        buffer.seek(0)
        return buffer.getvalue()

    # For CSV/JSON/TXT, if multiple sheets, concatenate with a label column
    if sheets:
        labeled = []
        for name, df in sheets.items():
            d = df.copy()
            d.insert(0, 'table', name)
            labeled.append(d)
        payload = pd.concat(labeled, ignore_index=True) if labeled else pd.DataFrame([{"message": "No data"}])
    else:
        payload = data  # type: ignore
        if getattr(payload, 'empty', True):
            payload = pd.DataFrame([{"message": "No data"}])

    if fmt == 'csv':
        buf = io.StringIO()
        payload.to_csv(buf, index=False)
        return buf.getvalue().encode('utf-8')
    if fmt == 'json':
        buf = io.StringIO()
        payload.to_json(buf, orient='records', force_ascii=False)
        return buf.getvalue().encode('utf-8')
    if fmt == 'txt':
        buf = io.StringIO()
        payload.to_csv(buf, index=False, sep='\t')
        return buf.getvalue().encode('utf-8')
    raise ValueError('Unsupported format')
