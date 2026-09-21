"""
AgriGo Production Session Service
Manages server-side sessions with secure token rotation, idle timeouts, and absolute expiry.
Stored in persistent SQLite sessions table with indexed lookups.
"""
import secrets
import datetime
import logging
from typing import Optional, Dict, Any, Tuple

from app.database import query_one, execute_db, get_db_connection

logger = logging.getLogger("agrigo.session")

# Session Configuration
ABSOLUTE_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days
IDLE_TIMEOUT_SECONDS = 2 * 3600          # 2 hours idle timeout
COOKIE_NAME = "agrigo_session"

class SessionService:
    @staticmethod
    def _now_utc() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def _now_iso() -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    @classmethod
    def create_session(
        cls,
        user_id: str,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new cryptographically secure session.
        If old_session_id is provided, rotates/invalidates it to prevent session fixation.
        """
        if old_session_id:
            cls.destroy_session(old_session_id)

        session_id = secrets.token_urlsafe(32)
        now = cls._now_utc()
        now_str = now.isoformat()
        expires_at = (now + datetime.timedelta(seconds=ABSOLUTE_EXPIRY_SECONDS)).isoformat()

        execute_db("""
            INSERT INTO sessions (id, user_id, role, ip_address, user_agent, created_at, last_accessed_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, role, ip_address or "", user_agent or "", now_str, now_str, expires_at))

        logger.info(f"[Session] Created session for user={user_id} role={role}")
        return {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "expires_at": expires_at,
            "max_age": ABSOLUTE_EXPIRY_SECONDS
        }

    @classmethod
    def get_session_and_user(cls, session_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Retrieves session, validates expiry & idle timeout, touches last_accessed_at,
        and retrieves active user record. Returns (session, user) or (None, None).
        """
        if not session_id or not isinstance(session_id, str):
            return None, None

        session_row = query_one("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if not session_row:
            return None, None

        session = dict(session_row)
        now = cls._now_utc()

        # Check absolute expiration
        try:
            expires_at = datetime.datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
            if now > expires_at:
                logger.info(f"[Session] Session {session_id[:8]}... absolutely expired")
                cls.destroy_session(session_id)
                return None, None
        except Exception as e:
            logger.error(f"[Session] Error parsing expires_at: {e}")
            cls.destroy_session(session_id)
            return None, None

        # Check idle timeout
        try:
            last_accessed = datetime.datetime.fromisoformat(session["last_accessed_at"].replace("Z", "+00:00"))
            if last_accessed.tzinfo is None:
                last_accessed = last_accessed.replace(tzinfo=datetime.timezone.utc)
            if (now - last_accessed).total_seconds() > IDLE_TIMEOUT_SECONDS:
                logger.info(f"[Session] Session {session_id[:8]}... idle timeout exceeded")
                cls.destroy_session(session_id)
                return None, None
        except Exception as e:
            logger.error(f"[Session] Error parsing last_accessed_at: {e}")
            cls.destroy_session(session_id)
            return None, None

        # Touch session last_accessed_at
        now_str = now.isoformat()
        execute_db("UPDATE sessions SET last_accessed_at = ? WHERE id = ?", (now_str, session_id))

        # Retrieve user record
        user_id = session["user_id"]
        role = session["role"]

        if role == "admin":
            user_row = query_one("SELECT id, email, full_name, role, is_2fa_enabled, created_at FROM admin_users WHERE id = ?", (user_id,))
            if user_row:
                user = dict(user_row)
                user["name"] = user.get("full_name")
                user["status"] = "active"
            else:
                user_row2 = query_one("SELECT id, phone as email, name, role, status, created_at FROM users WHERE id = ? AND role = 'admin'", (user_id,))
                if not user_row2:
                    cls.destroy_session(session_id)
                    return None, None
                user = dict(user_row2)
                user["full_name"] = user.get("name")
                user["is_2fa_enabled"] = 0
                user["status"] = user.get("status", "active")
        else:
            user_row = query_one("SELECT id, phone, name, preferred_language, state, district, village, status, role, created_at FROM users WHERE id = ?", (user_id,))
            if not user_row:
                cls.destroy_session(session_id)
                return None, None
            user = dict(user_row)
            user["role"] = user.get("role") or "farmer"
            # Verify user is not suspended
            if user.get("status") == "suspended":
                logger.warning(f"[Session] User {user_id} is suspended, rejecting session")
                cls.destroy_session(session_id)
                return None, None

        return session, user

    @classmethod
    def rotate_session(
        cls,
        old_session_id: str,
        user_id: str,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rotates session token after successful authentication to eliminate session fixation."""
        return cls.create_session(user_id, role, ip_address, user_agent, old_session_id=old_session_id)

    @classmethod
    def destroy_session(cls, session_id: str) -> bool:
        """Destroys a specific session in the database."""
        if not session_id:
            return False
        execute_db("DELETE FROM sessions WHERE id = ?", (session_id,))
        return True

    @classmethod
    def destroy_all_user_sessions(cls, user_id: str) -> int:
        """Destroys all active sessions for a user (e.g. upon password change, suspension, or deletion)."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            count = cur.rowcount
            conn.commit()
            return count
        finally:
            conn.close()

    @classmethod
    def cleanup_expired(cls) -> int:
        """Periodically purges expired sessions."""
        now_str = cls._now_iso()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE expires_at < ?", (now_str,))
            count = cur.rowcount
            conn.commit()
            return count
        finally:
            conn.close()
