from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from .utils import scrape_data, generate_file
import uuid
import os
from typing import Optional
import io

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/scrape")
async def scrape(
    url: str = Form(...),
    selector: Optional[str] = Form(None),
    format: str = Form(...),
    # Dynamic rendering options
    dynamic: Optional[str] = Form(None),
    wait_selector: Optional[str] = Form(None),
    wait_ms: Optional[str] = Form(None),
    # Pagination by query param
    page_param: Optional[str] = Form(None),
    page_start: Optional[str] = Form(None),
    page_end: Optional[str] = Form(None),
    # Pagination by next link selector
    next_selector: Optional[str] = Form(None),
    max_pages: Optional[str] = Form(None),
    delay_ms: Optional[str] = Form(None),
):
    # Basic validation for format
    allowed = {"csv", "xlsx", "json", "txt"}
    fmt = format.lower().strip()
    if fmt not in allowed:
        raise HTTPException(status_code=400, detail="Invalid format")

    # Helpers to parse optional ints and bool
    def to_int(v: Optional[str]) -> Optional[int]:
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        try:
            return int(v)
        except ValueError:
            return None

    def to_bool(v: Optional[str]) -> bool:
        if v is None:
            return False
        return v.strip().lower() in {"1", "true", "on", "yes"}

    # Validate URL scheme
    if not (url.startswith("http://") or url.startswith("https://")):
        return HTMLResponse("<h3>Invalid URL. Only http/https allowed.</h3>", status_code=400)

    # Scrape and generate file in-memory
    try:
        data = scrape_data(
            url,
            selector,
            dynamic=to_bool(dynamic),
            wait_selector=wait_selector,
            wait_ms=to_int(wait_ms),
            page_param=page_param,
            page_start=to_int(page_start),
            page_end=to_int(page_end),
            next_selector=next_selector,
            max_pages=to_int(max_pages),
            delay_ms=to_int(delay_ms),
        )
        file_bytes = generate_file(data, fmt)
    except Exception as e:
        return HTMLResponse(f"<h3>Scrape failed:</h3><pre>{str(e)}</pre>", status_code=500)

    # Map MIME types
    mime_map = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "txt": "text/plain",
    }
    media_type = mime_map.get(fmt, "application/octet-stream")
    filename = f"scraped.{fmt}"

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    # Check Redis for status
    # Simplified
    return {"job_id": job_id, "status": "completed"}  # Placeholder

@router.get("/result/{job_id}")
async def get_result(job_id: str):
    # Retrieve file from storage
    # Simplified
    file_path = f"temp/{job_id}.csv"  # Placeholder
    if os.path.exists(file_path):
        def iterfile():
            with open(file_path, 'rb') as f:
                yield from f
        return StreamingResponse(iterfile(), media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=data.csv"})
    raise HTTPException(status_code=404, detail="File not found")
