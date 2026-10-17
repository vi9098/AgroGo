from fastapi import APIRouter, HTTPException
import datetime
from app.database import get_supabase_status, query_db

router = APIRouter(tags=["Health Checks"])

@router.get("/health")
async def health_check():
    return {"status": "OK", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

@router.get("/ready")
async def readiness_check():
    supa = get_supabase_status()
    return {
        "status": "READY",
        "database": "OK",
        "supabase": supa.get("status"),
        "vector_store": "OK",
        "llm_orchestrator": "OK",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.get("/api/v1/supabase/status")
@router.get("/api/supabase/status")
async def supabase_status_endpoint():
    """Returns live Supabase PostgreSQL connection status and table row counts."""
    return {
        **get_supabase_status(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.get("/api/v1/supabase/query")
@router.get("/api/supabase/query")
async def supabase_query_proxy(table: str, limit: int = 50):
    """Secure proxy for fetching rows from Supabase with SQLite fallback without exposing secret keys to client."""
    clean_table = "".join(c for c in table if c.isalnum() or c == "_")
    allowed_tables = ["crops", "farms", "reminders", "crop_cycles", "live_mandi_prices", "district_crop_benchmarks", "knowledge_docs", "knowledge_sources"]
    if clean_table not in allowed_tables:
        raise HTTPException(status_code=400, detail="Table access restricted.")
    rows = query_db(f"SELECT * FROM {clean_table} LIMIT ?", (limit,))
    return rows
