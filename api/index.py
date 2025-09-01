# Vercel Python Serverless entrypoint
# Exposes a WSGI-compatible `app` by wrapping the FastAPI ASGI app
from asgiref.wsgi import AsgiToWsgi
from app.main import app as fastapi_app

# Wrap FastAPI ASGI app as WSGI for @vercel/python runtime
app = AsgiToWsgi(fastapi_app)
