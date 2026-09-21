"""
AgriGo Authentication & Authorization Middleware / Dependencies
Enforces server-side session checks, role-based access control (RBAC), and login rate limiting.
"""
from fastapi import Request, HTTPException, Depends
from typing import Optional, Dict, Any
import time
import logging

from app.services.session_service import SessionService, COOKIE_NAME

logger = logging.getLogger("agrigo.auth_middleware")

# In-memory sliding window rate limiter for login
class LoginRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, list] = {}  # key -> list of failure timestamps

    def _get_key(self, request: Request, identifier: str = "") -> str:
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        return f"{client_ip}:{identifier.strip().lower()}" if identifier else client_ip

    def check_rate_limit(self, request: Request, identifier: str = ""):
        key = self._get_key(request, identifier)
        now = time.time()
        timestamps = self.attempts.get(key, [])
        # Filter timestamps within current window
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]
        self.attempts[key] = valid_timestamps

        if len(valid_timestamps) >= self.max_attempts:
            remaining = int(self.window_seconds - (now - valid_timestamps[0]))
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed login attempts. Account temporarily locked for security. Please try again in {max(remaining, 1)} seconds."
            )

    def record_failure(self, request: Request, identifier: str = ""):
        key = self._get_key(request, identifier)
        now = time.time()
        timestamps = self.attempts.get(key, [])
        timestamps.append(now)
        self.attempts[key] = timestamps

    def record_success(self, request: Request, identifier: str = ""):
        key = self._get_key(request, identifier)
        self.attempts.pop(key, None)

login_limiter = LoginRateLimiter(max_attempts=5, window_seconds=300)


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extracts session cookie and retrieves validated user, or None."""
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        return None
    session, user = SessionService.get_session_and_user(session_id)
    if not session or not user:
        return None
    user["session_id"] = session["id"]
    return user


async def require_auth(request: Request) -> Dict[str, Any]:
    """
    Dependency: requires an active, unexpired, non-idle server-side session.
    Rejects with HTTP 401 if missing or invalid.
    """
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in to access this resource."
        )
    return user


async def require_admin(user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    """
    Dependency: requires authenticated user with 'admin' role.
    Unauthenticated -> 401 (via require_auth)
    Authenticated farmer -> 403 Forbidden
    Admin -> allowed
    """
    role = user.get("role", "")
    if role != "admin":
        logger.warning(f"[Security] Non-admin user {user.get('id')} attempted to access admin resource")
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Administrative privileges required."
        )
    return user


async def require_farmer(user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    """
    Dependency: requires authenticated user with 'farmer' or 'admin' role.
    """
    role = user.get("role", "")
    if role not in ["farmer", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Farmer access required."
        )
    return user


def verify_farmer_ownership(current_user: Dict[str, Any], requested_farmer_id: str):
    """
    IDOR Prevention Helper:
    Ensures that a farmer can only access and modify their own records.
    Admins are permitted to access any farmer record for management.
    """
    if current_user.get("role") == "admin":
        return
    if current_user.get("id") != requested_farmer_id:
        logger.warning(
            f"[IDOR Violation Blocked] User {current_user.get('id')} tried to access data for {requested_farmer_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access or modify another farmer's data."
        )
