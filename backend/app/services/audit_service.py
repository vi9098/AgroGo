import hashlib
import json
import datetime
from typing import List, Dict, Any
from app.database import execute_db, query_db
from app.models.audit import AuditLogEntry

class AuditService:
    @staticmethod
    async def log_event(
        actor_id: str,
        actor_type: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        ip_address: str = "127.0.0.1",
        details: dict = None
    ):
        ip_hash = hashlib.sha256((ip_address or "").encode()).hexdigest()[:16]
        details_json = json.dumps(details or {})
        now_str = datetime.datetime.utcnow().isoformat()
        
        execute_db("""
            INSERT INTO audit_logs (actor_id, actor_type, action, resource_type, resource_id, ip_hash, details_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (actor_id, actor_type, action, resource_type, resource_id, ip_hash, details_json, now_str))

    @staticmethod
    async def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
        rows = query_db("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
        for r in rows:
            if r.get("details_json"):
                try:
                    r["details"] = json.loads(r["details_json"])
                except Exception:
                    r["details"] = {}
        return rows
