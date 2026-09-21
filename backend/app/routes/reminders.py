from fastapi import APIRouter
from typing import List, Dict, Any
from app.database import query_db, execute_db
import uuid
import datetime

router = APIRouter(prefix="/reminders", tags=["Reminders"])

@router.get("/")
async def get_reminders():
    return query_db("SELECT * FROM reminders ORDER BY is_completed ASC, due_date ASC")

@router.post("/")
async def create_reminder(payload: Dict[str, Any]):
    rem_id = f"rem-{uuid.uuid4().hex[:8]}"
    now_str = datetime.datetime.utcnow().isoformat()
    execute_db("""
        INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (rem_id, payload.get("farmer_id", "farmer-1001"), payload.get("title", "Farm Task"), payload.get("description", ""), payload.get("due_date", "Today"), now_str))
    return {"id": rem_id, "success": True}
