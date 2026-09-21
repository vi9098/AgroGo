"""
AgriGo Python Serverless ASGI Entry Point for Vercel / Netlify / AWS Lambda.
Exposes the FastAPI application directly.
"""
import sys
import os

# Add backend directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

# Top-level ASGI handler for serverless runtimes
try:
    from mangum import Mangum
    handler = Mangum(app)
except Exception:
    handler = app
