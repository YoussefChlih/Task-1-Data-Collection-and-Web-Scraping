from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import router
from pathlib import Path

app = FastAPI(title="Web Scraper", version="1.0.0")

# Resolve absolute path for static dir; avoid crash if missing in serverless bundle
BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
	app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)
