from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import router
import os

app = FastAPI(title="Web Scraper", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)
