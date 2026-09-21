import sys
import os

# Ensure backend directory is in sys.path when imported as backend.app.main
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional

from app.config import settings
from app.database import connect_db, close_db
from app.middleware.security import SecurityHeadersMiddleware
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.voice import router as voice_router
from app.routes.media import router as media_router
from app.routes.knowledge import router as knowledge_router
from app.routes.admin import router as admin_router
from app.routes.farm import router as farm_router
from app.routes.reminders import router as reminders_router
from app.routes.health import router as health_router
from app.routes.agri import router as agri_router
from app.scripts.seed_data import seed_initial_knowledge

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    await seed_initial_knowledge()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Production-ready, secure, multilingual agricultural AI platform with session authentication and real telemetry.",
    lifespan=lifespan
)

# 1. Security Headers Middleware (Helmet equivalent for Python FastAPI)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Static files for uploaded media
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Core API Routers
API_PREFIX = "/api/v1"

# Public & System Health
app.include_router(health_router)

# Direct /api and /api/v1 Auth Routers
app.include_router(auth_router)

# Direct /api and /api/v1 Admin Routers (Protected by require_admin)
app.include_router(admin_router)

# Direct /api/weather endpoint
@app.get("/api/weather", tags=["Agriculture & Knowledge"])
async def get_direct_weather(lat: Optional[float] = None, lon: Optional[float] = None):
    """Direct real-time agricultural weather endpoint."""
    from app.adapters.weather import WeatherProviderAdapter
    return await WeatherProviderAdapter.get_agricultural_weather(lat, lon)

# Domain Routers
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(voice_router, prefix=API_PREFIX)
app.include_router(media_router, prefix=API_PREFIX)
app.include_router(knowledge_router, prefix=API_PREFIX)
app.include_router(farm_router, prefix=API_PREFIX)
app.include_router(reminders_router, prefix=API_PREFIX)
app.include_router(agri_router)

# Mount Pure HTML, CSS, JavaScript Frontend at root for instant zero-dependency execution
FRONTEND_HTML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend-html"))
if os.path.exists(FRONTEND_HTML_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_HTML_DIR, html=True), name="frontend-html")

# Vercel / Serverless ASGI Handler via Mangum
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
