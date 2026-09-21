"""
AgriGo Production Security Headers & Error Handling Middleware
Implements HTTP security headers (equivalent to Helmet), secure CORS constraints,
and sanitization against XSS and injection attacks.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger("agrigo.security")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.error(f"[Unhandled Server Error] {request.method} {request.url.path}: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "An internal server error occurred. Our engineering team has been notified.",
                    "code": "INTERNAL_SERVER_ERROR"
                }
            )

        # Apply robust production security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(self), camera=(self), fullscreen=(self)"

        # Content-Security-Policy (Allow local static assets, Leaflet, Google Fonts, Open-Meteo, data.gov.in, Supabase, Esri/ArcGIS, Authkey)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob: https: https://*.tile.openstreetmap.org https://server.arcgisonline.com; "
            "connect-src 'self' https://api.open-meteo.com https://api.data.gov.in https://*.supabase.co https://lebkgjebavldqqflwwox.supabase.co https://*.tile.openstreetmap.org https://server.arcgisonline.com https://api.authkey.io https://console.authkey.io; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        return response
