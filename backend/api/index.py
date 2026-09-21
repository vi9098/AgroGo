"""
AgriGo Python Serverless ASGI Entry Point for Vercel / Netlify / AWS Lambda.
Exposes the FastAPI application directly.
"""
import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app

# Top-level ASGI handler for serverless runtimes
try:
    from mangum import Mangum
    handler = Mangum(app)
except Exception:
    handler = app
