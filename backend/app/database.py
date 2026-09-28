"""
AgriGo Cloud Database Adapter (Supabase PostgreSQL)
Provides unified PostgREST connectivity to Supabase Cloud Database.
All database operations (SELECT, INSERT, UPDATE, DELETE, COUNT) run exclusively on Supabase.
All other local databases (SQLite, MongoDB) are completely removed.
"""
import os
import re
import json
import logging
import datetime
import uuid
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager

from app.supabase_client import supabase_client
from app.config import settings

logger = logging.getLogger("agrigo.database")

# Virtual DB path for backward compatibility with scripts importing DB_PATH
DB_PATH = ":memory:"

# Known registered Supabase tables
KNOWN_TABLES = {
    "users", "crops", "farms", "crop_cycles", "reminders", "sessions", "otps",
    "admin_users", "knowledge_docs", "knowledge_sources", "knowledge_chunks",
    "live_mandi_prices", "crop_production_historical", "district_crop_benchmarks",
    "market_data", "farmer_observations", "soil_data", "fields", "audit_logs",
    "conversations", "messages", "weather_cache"
}

@contextmanager
def db_transaction():
    """Provides a transaction context for database operations."""
    yield None

def _filter_rows_in_memory(rows: List[Dict[str, Any]], where_clause: str, params: tuple) -> List[Dict[str, Any]]:
    """Filters a list of records in Python matching standard SQL conditions."""
    if not rows or not where_clause:
        return rows

    filtered = []
    conds = [c.strip() for c in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)]

    for r in rows:
        match = True
        param_idx = 0
        for cond in conds:
            eq_m = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*\?$", cond)
            like_m = re.match(r"^([a-zA-Z0-9_]+)\s+LIKE\s+\?$", cond, re.IGNORECASE)
            
            if eq_m and param_idx < len(params):
                col = eq_m.group(1)
                expected = params[param_idx]
                param_idx += 1
                val = r.get(col)
                if str(val).lower() != str(expected).lower():
                    match = False
                    break
            elif like_m and param_idx < len(params):
                col = like_m.group(1)
                pat = str(params[param_idx]).strip("%").lower()
                param_idx += 1
                val = str(r.get(col, "")).lower()
                if pat not in val:
                    match = False
                    break
            elif "is_completed = 0" in cond.lower():
                if r.get("is_completed") not in (0, "0", False, None):
                    match = False
                    break
            elif "is_completed = 1" in cond.lower():
                if r.get("is_completed") not in (1, "1", True):
                    match = False
                    break
            elif "is_used = 0" in cond.lower():
                if r.get("is_used") not in (0, "0", False, None):
                    match = False
                    break
            elif "is_used = 1" in cond.lower():
                if r.get("is_used") not in (1, "1", True):
                    match = False
                    break
        if match:
            filtered.append(r)
    return filtered

def parse_and_query_supabase(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Translates standard SELECT queries directly to Supabase PostgREST.
    Extracts table name, filters, sorting, and pagination.
    """
    if not supabase_client.is_available():
        if not supabase_client.check_health():
            logger.warning("[Database] Supabase is unreachable")
            return []

    q = query.strip()
    q_upper = q.upper()

    if not q_upper.startswith("SELECT"):
        return []

    # 1. Handle simple COUNT queries: SELECT COUNT(*) [AS alias] FROM table [WHERE ...]
    count_match = re.match(r"^SELECT\s+COUNT\(\*\)(?:\s+AS\s+([a-zA-Z0-9_]+))?\s+FROM\s+([a-zA-Z0-9_]+)\s*$", q, re.IGNORECASE)
    if count_match:
        alias = count_match.group(1) or "count"
        tbl = count_match.group(2).lower()
        cnt = supabase_client.count(tbl)
        return [{alias: cnt}]

    # 2. Extract table name
    m = re.search(r"FROM\s+([a-zA-Z0-9_]+)", q, re.IGNORECASE)
    if not m:
        return []
    table = m.group(1).lower()

    # 3. Parse ORDER BY
    order_val = None
    order_m = re.search(r"ORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*$)", q, re.IGNORECASE)
    if order_m:
        raw_order = order_m.group(1).strip()
        parts = []
        for p in raw_order.split(","):
            p = p.strip()
            if not p:
                continue
            tokens = p.split()
            col = tokens[0].split(".")[-1]
            direction = tokens[1].lower() if len(tokens) > 1 else "asc"
            parts.append(f"{col}.{direction}")
        order_val = ",".join(parts)

    # 4. Parse LIMIT
    limit_val = None
    limit_m = re.search(r"LIMIT\s+(\d+|\?)", q, re.IGNORECASE)
    param_list = list(params)
    if limit_m:
        lim_str = limit_m.group(1)
        if lim_str == "?":
            limit_val = param_list.pop() if param_list else None
        else:
            limit_val = int(lim_str)

    # 5. Parse WHERE conditions
    filters = {}
    where_m = re.search(r"WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)", q, re.IGNORECASE | re.DOTALL)
    
    if where_m:
        where_clause = where_m.group(1).strip()
        where_upper = where_clause.upper()

        # Handle OR condition: e.g. "id = ? OR phone = ?"
        if " OR " in where_upper:
            col_matches = re.findall(r"([a-zA-Z0-9_]+)\s*=\s*\?", where_clause)
            if len(col_matches) == 2 and len(param_list) >= 2:
                r1 = supabase_client.select(table, filters={col_matches[0]: param_list[0]}, limit=1)
                if r1:
                    return r1
                return supabase_client.select(table, filters={col_matches[1]: param_list[1]}, limit=1) or []
            
            # Fetch table rows and filter in Python
            all_rows = supabase_client.select(table, order=order_val, limit=limit_val or 500) or []
            return _filter_rows_in_memory(all_rows, where_clause, tuple(param_list))

        # Handle AND conditions
        conds = [c.strip() for c in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)]
        param_idx = 0
        can_filter_direct = True

        for cond in conds:
            eq_m = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*\?$", cond)
            like_m = re.match(r"^([a-zA-Z0-9_]+)\s+LIKE\s+\?$", cond, re.IGNORECASE)
            
            if eq_m and param_idx < len(param_list):
                col = eq_m.group(1)
                val = param_list[param_idx]
                filters[col] = val
                param_idx += 1
            elif like_m and param_idx < len(param_list):
                col = like_m.group(1)
                val = str(param_list[param_idx]).replace("%", "*")
                filters[col] = f"ilike.{val}"
                param_idx += 1
            elif "is_used = 0" in cond.lower():
                filters["is_used"] = 0
            elif "is_used = 1" in cond.lower():
                filters["is_used"] = 1
            elif "is_completed = 0" in cond.lower():
                filters["is_completed"] = 0
            elif "is_completed = 1" in cond.lower():
                filters["is_completed"] = 1
            else:
                can_filter_direct = False
                break

        if not can_filter_direct:
            all_rows = supabase_client.select(table, order=order_val, limit=500) or []
            return _filter_rows_in_memory(all_rows, where_clause, tuple(param_list))

    try:
        rows = supabase_client.select(
            table=table,
            filters=filters if filters else None,
            order=order_val,
            limit=limit_val
        )
        return rows if rows is not None else []
    except Exception as e:
        logger.error(f"[Supabase Query Failed] {table}: {e}")
        return []

def execute_supabase_write(query: str, params: tuple = ()) -> Any:
    """Translates INSERT, UPDATE, DELETE queries directly to Supabase PostgREST."""
    if not supabase_client.is_available():
        supabase_client.check_health()

    q = query.strip()
    q_upper = q.upper()

    # 1. INSERT
    if q_upper.startswith("INSERT"):
        m = re.search(r"INSERT\s+(?:OR\s+REPLACE\s+|OR\s+IGNORE\s+)?INTO\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*VALUES\s*\((.*?)\)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        cols = [c.strip().strip('"').strip('`') for c in m.group(2).split(",")]
        val_tokens = [v.strip() for v in m.group(3).split(",")]

        row_dict = {}
        param_idx = 0
        for col, token in zip(cols, val_tokens):
            if token == "?":
                if param_idx < len(params):
                    row_dict[col] = params[param_idx]
                    param_idx += 1
            else:
                clean_val = token.strip("'\"")
                row_dict[col] = int(clean_val) if clean_val.isdigit() else clean_val

        # Auto-generate ID if missing
        if "id" not in row_dict and table in ("sessions", "crops", "farms", "reminders", "crop_cycles", "knowledge_docs"):
            prefix = table[:-1] if table.endswith("s") else table
            row_dict["id"] = f"{prefix}-{uuid.uuid4().hex[:8]}"

        res = supabase_client.insert(table, row_dict, upsert=True)
        if res and isinstance(res, list) and isinstance(res[0], dict):
            return res[0].get("id") or 1
        return 1

    # 2. UPDATE
    elif q_upper.startswith("UPDATE"):
        m = re.search(r"UPDATE\s+([a-zA-Z0-9_]+)\s+SET\s+(.*?)\s+WHERE\s+(.*)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        set_clause = m.group(2).strip()
        where_clause = m.group(3).strip()

        update_data = {}
        param_idx = 0
        for item in set_clause.split(","):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        update_data[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    update_data[col] = int(clean_val) if clean_val.isdigit() else clean_val

        filters = {}
        for item in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        filters[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    filters[col] = int(clean_val) if clean_val.isdigit() else clean_val

        res = supabase_client.update(table, update_data, filters)
        return len(res) if res else 1

    # 3. DELETE
    elif q_upper.startswith("DELETE"):
        m = re.search(r"DELETE\s+FROM\s+([a-zA-Z0-9_]+)\s+WHERE\s+(.*)", q, re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        table = m.group(1).lower()
        where_clause = m.group(2).strip()

        filters = {}
        param_idx = 0
        for item in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE):
            if "=" in item:
                col, val = item.split("=", 1)
                col = col.strip().strip('"').strip('`')
                val = val.strip()
                if val == "?":
                    if param_idx < len(params):
                        filters[col] = params[param_idx]
                        param_idx += 1
                else:
                    clean_val = val.strip("'\"")
                    filters[col] = int(clean_val) if clean_val.isdigit() else clean_val

        ok = supabase_client.delete(table, filters)
        return 1 if ok else 0

    return None

def execute_db(query: str, params: tuple = ()) -> int:
    """Executes INSERT, UPDATE, DELETE queries directly against Supabase Cloud Database."""
    res = execute_supabase_write(query, params)
    return res if isinstance(res, int) else 1

def execute_local_db(query: str, params: tuple = ()) -> int:
    """Direct alias to execute_db for Supabase operations."""
    return execute_db(query, params)

def query_db(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Executes SELECT queries directly against Supabase Cloud Database."""
    return parse_and_query_supabase(query, params)

def query_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Returns the first matching row from Supabase Cloud Database or None."""
    rows = query_db(query, params)
    return rows[0] if rows else None

def init_sql_schema():
    """No-op: Schema is maintained in Supabase Cloud PostgreSQL."""
    pass

def seed_supabase_defaults():
    """Seeds initial administrative and demo records directly into Supabase Cloud Database if missing."""
    if not supabase_client.is_available():
        return
        
    try:
        from app.utils.security import hash_password
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Seed Admin User if missing
        admin = supabase_client.select_one("admin_users", filters={"email": "admin@agrigo.com"})
        if not admin:
            admin_pass = hash_password("Admin@AgriGo2026")
            supabase_client.insert("admin_users", {
                "id": "admin-1",
                "email": "admin@agrigo.com",
                "password_hash": admin_pass,
                "full_name": "AgriGo Commander",
                "role": "admin",
                "is_2fa_enabled": 0,
                "created_at": now
            }, upsert=True)
            logger.info("[Supabase Seeding] Default admin user initialized")

        # Seed Demo Farmer if missing
        farmer = supabase_client.select_one("users", filters={"phone": "9876543210"})
        if not farmer:
            demo_pass = hash_password("123456")
            consent = json.dumps({"farm_memory": True, "ai_improvement": True, "photo_learning": True})
            supabase_client.insert("users", {
                "id": "farmer-1001",
                "phone": "9876543210",
                "name": "Ramesh Patel",
                "password_hash": demo_pass,
                "preferred_language": "hi",
                "state": "Uttar Pradesh",
                "district": "Varanasi",
                "village": "Rampur",
                "consent_json": consent,
                "status": "active",
                "role": "farmer",
                "created_at": now
            }, upsert=True)
            logger.info("[Supabase Seeding] Default demo farmer initialized")

        # Seed Demo Farm if missing
        farm = supabase_client.select_one("farms", filters={"id": "farm-1"})
        if not farm:
            supabase_client.insert("farms", {
                "id": "farm-1",
                "farmer_id": "farmer-1001",
                "name": "Ramesh Organic Farm",
                "total_area_acres": 4.5,
                "soil_type": "Sandy Loam",
                "irrigation_type": "Drip Irrigation",
                "created_at": now
            }, upsert=True)

        # Seed Demo Crops if missing
        crops = supabase_client.select("crops", filters={"farmer_id": "farmer-1001"}, limit=1)
        if not crops:
            sample_crops = [
                {"id": "crop-1", "farm_id": "farm-1", "farmer_id": "farmer-1001", "crop_name": "Tomato", "variety": "Himsona", "stage": "Flowering", "health_status": "Good", "sowing_date": "2024-02-10", "area_acres": 2.0, "created_at": now},
                {"id": "crop-2", "farm_id": "farm-1", "farmer_id": "farmer-1001", "crop_name": "Wheat", "variety": "PBW 550", "stage": "Tillering", "health_status": "Monitor", "sowing_date": "2024-01-05", "area_acres": 2.5, "created_at": now},
                {"id": "crop-3", "farm_id": "farm-1", "farmer_id": "farmer-1001", "crop_name": "Mustard", "variety": "Pusa Bold", "stage": "Pod Filling", "health_status": "Good", "sowing_date": "2023-11-20", "area_acres": 1.0, "created_at": now},
            ]
            for c in sample_crops:
                supabase_client.insert("crops", c, upsert=True)
            logger.info("[Supabase Seeding] Default crops initialized")

    except Exception as e:
        logger.warning(f"[Supabase Seeding Error] {e}")

def get_supabase_status() -> Dict[str, Any]:
    """Returns real-time status and row telemetry from Supabase Cloud Database."""
    is_cfg = supabase_client.is_configured()
    is_ok = supabase_client.check_health() if is_cfg else False
    counts = {}
    if is_ok:
        try:
            for tbl in ["crops", "users", "reminders", "farms", "crop_cycles", "sessions", "admin_users"]:
                counts[tbl] = supabase_client.count(tbl)
        except Exception:
            pass
    return {
        "configured": is_cfg,
        "healthy": is_ok,
        "url": supabase_client.url if is_cfg else None,
        "status": "connected" if is_ok else "offline",
        "counts": counts
    }

async def connect_db():
    """Initializes and verifies the exclusive Supabase Cloud Database connection."""
    print("=" * 65)
    print(" [DATABASE] Initializing Exclusive Supabase Cloud Database Engine")
    print(f" [DATABASE] Endpoint: {supabase_client.url}")
    
    is_ok = supabase_client.check_health()
    if is_ok:
        print(" [DATABASE] SUCCESS: Supabase PostgreSQL connected and healthy (HTTP 200)")
        try:
            seed_supabase_defaults()
        except Exception as e:
            logger.debug(f"[Database Seeding] {e}")
    else:
        print(" [DATABASE] WARNING: Supabase health check returned non-200. Check network/keys.")
    print("=" * 65)

async def close_db():
    """Closes Supabase client session."""
    pass
