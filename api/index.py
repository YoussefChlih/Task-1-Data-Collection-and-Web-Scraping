# Vercel Python Serverless entrypoint
"""
Expose the FastAPI ASGI app directly. Vercel's Python runtime can load an ASGI
callable named `app` without needing an adapter.
"""
from app.main import app as app
