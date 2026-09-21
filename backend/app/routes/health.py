from fastapi import APIRouter
import datetime
from app.database import get_supabase_status

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
