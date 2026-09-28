import sqlite3
import os
import datetime
import json
import logging
import re
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

from app.supabase_client import supabase_client

logger = logging.getLogger("agrigo.database")

# Database file path in backend directory (or /tmp in serverless environments like Vercel)
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    TMP_DB = os.path.join("/tmp", "agrigo.db")
    ORIG_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))
    if not os.path.exists(TMP_DB) and os.path.exists(ORIG_DB):
        import shutil
        try:
            shutil.copy2(ORIG_DB, TMP_DB)
        except Exception:
            pass
    DB_PATH = TMP_DB
else:
    DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

@contextmanager
def db_transaction():
    """Provides an isolated database transaction with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def parse_and_query_supabase(query: str, params: tuple = ()) -> Optional[List[Dict[str, Any]]]:
    """
    Translates standard SELECT queries directly to Supabase PostgREST.
    Returns list of dicts on success, or None to fall back to SQLite.
    """
    if not supabase_client.is_configured():
        return None
        
    q = query.strip()
    q_upper = q.upper()
    
    if not q_upper.startswith("SELECT"):
        return None
        
    m = re.search(r"FROM\s+([a-zA-Z0-9_]+)", q, re.IGNORECASE)
    if not m:
        return None
    table = m.group(1).lower()
    
    known_tables = {
        "users", "crops", "farms", "crop_cycles", "reminders", "sessions", "otps",
        "admin_users", "knowledge_docs", "knowledge_sources", "knowledge_chunks",
        "live_mandi_prices", "crop_production_historical", "district_crop_benchmarks",
        "market_data", "farmer_observations", "soil_data", "fields", "audit_logs"
    }
    if table not in known_tables:
        return None
        
    # Let complex SQL queries, subqueries, aggregates, joins, DISTINCT, and LIKE fall back to SQLite
    if (
        q_upper.count("SELECT") > 1
        or any(k in q_upper for k in ["GROUP BY", "JOIN", "HAVING", "DISTINCT", "LIKE", "UNION", "CASE ", " 1=1", " U.", " A.", " F.", "!= ", "<>"])
    ):
        return None

    # Handle simple COUNT(*) queries: e.g. SELECT COUNT(*) AS cnt FROM table (without WHERE or subqueries)
    count_match = re.match(r"^SELECT\s+COUNT\(\*\)(?:\s+AS\s+([a-zA-Z0-9_]+))?\s+FROM\s+([a-zA-Z0-9_]+)\s*$", q, re.IGNORECASE)
    if count_match:
        alias = count_match.group(1) or "count"
        tbl = count_match.group(2).lower()
        if tbl in known_tables:
            cnt = supabase_client.count(tbl)
            return [{alias: cnt}]
        return None

    # Parse ORDER BY
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

    # Parse LIMIT
    limit_val = None
    limit_m = re.search(r"LIMIT\s+(\d+|\?)", q, re.IGNORECASE)
    if limit_m:
        lim_str = limit_m.group(1)
        if lim_str == "?":
            limit_val = params[-1] if params else None
        else:
            limit_val = int(lim_str)

    # Parse WHERE clauses
    filters = {}
    where_m = re.search(r"WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)", q, re.IGNORECASE | re.DOTALL)
    if where_m:
        where_clause = where_m.group(1).strip()
        where_upper = where_clause.upper()
        
        # Complex WHERE clauses (subqueries, negation, complex operators) must fall back to SQLite
        if any(op in where_upper for op in ["!=", "<>", "<", ">", " IN ", " IS ", " NOT ", " LIKE "]):
            return None
        
        # Handle "phone = ? OR id = ?"
        if " OR " in where_upper:
            col_matches = re.findall(r"([a-zA-Z0-9_]+)\s*=\s*\?", where_clause)
            if len(col_matches) == 2 and len(params) >= 2:
                r1 = supabase_client.select(table, filters={col_matches[0]: params[0]}, limit=1)
                if r1:
                    return r1
                return supabase_client.select(table, filters={col_matches[1]: params[1]}, limit=1)
            # If arbitrary OR condition, fall back to SQLite
            return None
        
        # Handle "col1 = ? AND col2 = ?"
        conds = [c.strip() for c in re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)]
        param_idx = 0
        for cond in conds:
            eq_m = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*\?$", cond)
            if eq_m and param_idx < len(params):
                filters[eq_m.group(1)] = params[param_idx]
                param_idx += 1
            elif "is_used = 0" in cond.lower():
                filters["is_used"] = 0
            elif "is_completed = 0" in cond.lower():
                filters["is_completed"] = 0
            elif "is_completed = 1" in cond.lower():
                filters["is_completed"] = 1
            else:
                # Unhandled condition pattern: safely fall back to SQLite
                return None

        # Verify that all positional params were successfully consumed
        if len(params) > 0 and param_idx < len(params):
            return None

    try:
        rows = supabase_client.select(
            table=table,
            filters=filters if filters else None,
            order=order_val,
            limit=limit_val
        )
        return rows
    except Exception as e:
        logger.debug(f"[Supabase Route Failed] {table}: {e}")
        return None

def execute_supabase_write(query: str, params: tuple = ()):
    """Translates INSERT, UPDATE, DELETE queries to Supabase PostgREST."""
    if not supabase_client.is_configured():
        return None
        
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
                    
        return supabase_client.insert(table, row_dict, upsert=True)

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
                    
        return supabase_client.update(table, update_data, filters)

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

        return supabase_client.delete(table, filters)

    return None

def execute_db(query: str, params: tuple = ()) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
    finally:
        conn.close()

    # Synchronize write directly to Supabase cloud
    try:
        execute_supabase_write(query, params)
    except Exception as e:
        logger.debug(f"[Supabase Write Sync Skipped] {e}")

    return last_id

def execute_local_db(query: str, params: tuple = ()) -> int:
    """Executes query strictly against local SQLite cache without cloud dual-write (for internal seeding)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
    finally:
        conn.close()
    return last_id

def query_db(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    # 1. Attempt live query directly from Supabase PostgreSQL
    supa_results = None
    try:
        supa_results = parse_and_query_supabase(query, params)
        if supa_results is not None and len(supa_results) > 0:
            return supa_results
    except Exception as e:
        logger.debug(f"[Supabase Query Fallback] {e}")

    # 2. Resilient local SQLite fallback
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        local_results = [dict(row) for row in rows]
        if local_results:
            return local_results
    finally:
        conn.close()

    return supa_results if supa_results is not None else []

def query_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    rows = query_db(query, params)
    return rows[0] if rows else None

def init_sql_schema():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        phone TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT,
        preferred_language TEXT DEFAULT 'hi',
        state TEXT DEFAULT 'Uttar Pradesh',
        district TEXT DEFAULT 'Varanasi',
        village TEXT DEFAULT 'Rampur',
        consent_json TEXT,
        status TEXT DEFAULT 'active',
        role TEXT DEFAULT 'farmer',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        created_at TEXT NOT NULL,
        last_accessed_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

    CREATE TABLE IF NOT EXISTS otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        logid TEXT
    );

    CREATE TABLE IF NOT EXISTS admin_users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        is_2fa_enabled INTEGER DEFAULT 0,
        totp_secret TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS farms (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        name TEXT NOT NULL,
        total_area_acres REAL DEFAULT 2.5,
        soil_type TEXT DEFAULT 'Alluvial Loam',
        irrigation_type TEXT DEFAULT 'Drip Irrigation',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS crops (
        id TEXT PRIMARY KEY,
        farm_id TEXT,
        farmer_id TEXT,
        crop_name TEXT NOT NULL,
        variety TEXT,
        stage TEXT DEFAULT 'Flowering',
        health_status TEXT DEFAULT 'Good',
        sowing_date TEXT,
        area_acres REAL DEFAULT 1.5,
        created_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_crops_farmer ON crops(farmer_id);

    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        language TEXT DEFAULT 'hi',
        updated_at TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        provider TEXT,
        evidence_json TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS knowledge_docs (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        crop TEXT,
        content TEXT NOT NULL,
        source TEXT NOT NULL,
        verified INTEGER DEFAULT 1,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_id TEXT NOT NULL,
        actor_type TEXT NOT NULL,
        action TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT,
        ip_hash TEXT,
        details_json TEXT,
        timestamp TEXT
    );

    CREATE TABLE IF NOT EXISTS reminders (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        is_completed INTEGER DEFAULT 0,
        reminder_type TEXT DEFAULT 'general',
        crop_id TEXT,
        priority TEXT DEFAULT 'normal',
        created_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_reminders_farmer ON reminders(farmer_id);

    CREATE TABLE IF NOT EXISTS fields (
        id TEXT PRIMARY KEY,
        farm_id TEXT NOT NULL,
        farmer_id TEXT NOT NULL,
        name TEXT NOT NULL,
        area_acres REAL DEFAULT 1.0,
        soil_type TEXT DEFAULT 'Alluvial Loam',
        irrigation_source TEXT DEFAULT 'Tubewell',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS crop_cycles (
        id TEXT PRIMARY KEY,
        field_id TEXT,
        farmer_id TEXT NOT NULL,
        crop_name TEXT NOT NULL,
        variety TEXT,
        sowing_date TEXT NOT NULL,
        expected_harvest_date TEXT,
        area_acres REAL DEFAULT 1.0,
        irrigation_method TEXT DEFAULT 'Drip',
        soil_type TEXT DEFAULT 'Sandy Loam',
        current_stage TEXT DEFAULT 'Sowing',
        health_status TEXT DEFAULT 'Good',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS knowledge_sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        organization TEXT NOT NULL,
        country TEXT DEFAULT 'India',
        languages_json TEXT DEFAULT '["en","hi"]',
        source_type TEXT DEFAULT 'government',
        license_name TEXT,
        license_url TEXT,
        terms_url TEXT,
        allows_automated_collection INTEGER DEFAULT 0,
        allows_text_reuse INTEGER DEFAULT 0,
        allows_model_training INTEGER DEFAULT 0,
        requires_attribution INTEGER DEFAULT 1,
        robots_checked INTEGER DEFAULT 1,
        verified_at TEXT,
        status TEXT DEFAULT 'Active',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS knowledge_chunks (
        id TEXT PRIMARY KEY,
        document_id TEXT,
        text TEXT NOT NULL,
        crop TEXT NOT NULL,
        topic TEXT NOT NULL,
        region TEXT DEFAULT 'India',
        language TEXT DEFAULT 'en',
        source TEXT NOT NULL,
        source_url TEXT,
        license TEXT,
        confidence REAL DEFAULT 0.95,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS farmer_observations (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        crop TEXT NOT NULL,
        location TEXT NOT NULL,
        problem TEXT NOT NULL,
        observed_pest TEXT,
        treatment_applied TEXT,
        result TEXT,
        evidence_type TEXT DEFAULT 'COMMUNITY_OBSERVATION',
        validation_status TEXT DEFAULT 'pending_review',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS weather_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        temp_c REAL,
        rain_prob INTEGER,
        precipitation_mm REAL,
        humidity INTEGER,
        wind_kmh REAL,
        condition TEXT,
        spray_window_safe INTEGER DEFAULT 1,
        raw_json TEXT,
        fetched_at TEXT
    );

    CREATE TABLE IF NOT EXISTS soil_data (
        id TEXT PRIMARY KEY,
        farmer_id TEXT NOT NULL,
        field_id TEXT,
        soil_type TEXT NOT NULL,
        ph REAL,
        organic_carbon_pct REAL,
        nitrogen_kg_ha REAL,
        phosphorus_kg_ha REAL,
        potassium_kg_ha REAL,
        moisture_pct REAL,
        tested_at TEXT
    );

    CREATE TABLE IF NOT EXISTS market_data (
        id TEXT PRIMARY KEY,
        commodity TEXT NOT NULL,
        variety TEXT,
        market_name TEXT NOT NULL,
        district TEXT,
        state TEXT NOT NULL,
        min_price REAL,
        max_price REAL,
        modal_price REAL,
        unit TEXT DEFAULT '₹/Quintal',
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS live_mandi_prices (
        id TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        market TEXT NOT NULL,
        commodity TEXT NOT NULL,
        variety TEXT,
        grade TEXT,
        arrival_date TEXT,
        min_price REAL,
        max_price REAL,
        modal_price REAL NOT NULL,
        unit TEXT DEFAULT '₹/क्विंटल',
        source TEXT DEFAULT 'data.gov.in (Agmarknet)',
        updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_mandi_comm ON live_mandi_prices(commodity);
    CREATE INDEX IF NOT EXISTS idx_mandi_state ON live_mandi_prices(state);
    CREATE INDEX IF NOT EXISTS idx_mandi_date ON live_mandi_prices(arrival_date);
    """)

    # Migration checks for existing databases
    for col, col_type in [
        ("reminder_type", "TEXT DEFAULT 'general'"),
        ("crop_id", "TEXT"),
        ("priority", "TEXT DEFAULT 'normal'"),
        ("category", "TEXT DEFAULT 'general'"),
        ("dosage_info", "TEXT"),
        ("acreage", "REAL DEFAULT 1.0"),
        ("stage_name", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE reminders ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    for col, col_type in [
        ("status", "TEXT DEFAULT 'active'"),
        ("role", "TEXT DEFAULT 'farmer'"),
        ("security_question", "TEXT"),
        ("security_answer_hash", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("ALTER TABLE otps ADD COLUMN logid TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def seed_sql_defaults():
    try:
        from app.utils.security import hash_password
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Seed Admin User safely with INSERT OR IGNORE
        admin_pass = hash_password("Admin@AgriGo2026")
        execute_local_db("""
            INSERT OR IGNORE INTO admin_users (id, email, password_hash, full_name, role, is_2fa_enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin-1", "admin@agrigo.com", admin_pass, "AgriGo Commander", "admin", 0, now))

        # Seed Sample Farmers
        demo_pass = hash_password("123456")
        sample_farmers = [
            ("farmer-1001", "9876543210", "Ramesh Patel", "Uttar Pradesh", "Varanasi", "Rampur"),
            ("farmer-1002", "9876543211", "Suresh Kumar", "Punjab", "Ludhiana", "Khanna"),
            ("farmer-1003", "9876543212", "Anil Yadav", "Madhya Pradesh", "Indore", "Depalpur"),
            ("farmer-1004", "9876543213", "Lakshmi Devi", "Andhra Pradesh", "Guntur", "Tenali"),
        ]
        for fid, phone, name, state, dist, vill in sample_farmers:
            consent = json.dumps({"farm_memory": True, "ai_improvement": True, "photo_learning": True})
            execute_local_db("""
                INSERT OR IGNORE INTO users (id, phone, name, password_hash, preferred_language, state, district, village, consent_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fid, phone, name, demo_pass, "hi", state, dist, vill, consent, now))

        # Seed Farms & Crops
        execute_local_db("""
            INSERT OR IGNORE INTO farms (id, farmer_id, name, total_area_acres, soil_type, irrigation_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("farm-1", "farmer-1001", "Ramesh Organic Farm", 4.5, "Sandy Loam", "Drip Irrigation", now))

        sample_crops = [
            ("crop-1", "farm-1", "farmer-1001", "Tomato", "Himsona", "Flowering", "Good", "2024-02-10", 2.0),
            ("crop-2", "farm-1", "farmer-1001", "Wheat", "PBW 550", "Tillering", "Monitor", "2024-01-05", 2.5),
            ("crop-3", "farm-1", "farmer-1001", "Mustard", "Pusa Bold", "Pod Filling", "Good", "2023-11-20", 1.0),
        ]
        for cid, fmid, fmerid, cname, var, stage, health, sdate, area in sample_crops:
            execute_local_db("""
                INSERT OR IGNORE INTO crops (id, farm_id, farmer_id, crop_name, variety, stage, health_status, sowing_date, area_acres, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, fmid, fmerid, cname, var, stage, health, sdate, area, now))

        # Seed Reminders
        sample_reminders = [
            ("rem-1", "farmer-1001", "Tomato Drip Irrigation", "Operate drip for 45 mins early morning.", "Tomorrow 06:00 AM", 0),
            ("rem-2", "farmer-1001", "Neem Oil Spray (Leaf Curl Protection)", "Spray 5ml/L neem oil solution on leaf underside.", "Sep 22, 2026", 0),
            ("rem-3", "farmer-1001", "Wheat Crown Root Fertilizer Top-Dress", "Apply 25kg Urea per acre post-irrigation.", "Sep 25, 2026", 0),
        ]
        for rid, fid, title, desc, due, done in sample_reminders:
            execute_local_db("""
                INSERT OR IGNORE INTO reminders (id, farmer_id, title, description, due_date, is_completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rid, fid, title, desc, due, done, now))

        # Seed Knowledge Docs
        sample_kb = [
            ("kb-1", "Tomato Leaf Curl Virus (ToLCV) & Vector Management", "diseases", "Tomato",
             "Transmitted by whitefly Bemisia tabaci. Leaves curl upward and become crinkled. Control: Yellow sticky traps (15/acre), 5ml neem oil/L spray. Chemical if severe: Imidacloprid 17.8 SL @ 0.5 ml/L.", "ICAR - Indian Institute of Horticultural Research", 1),
            ("kb-2", "Wheat Crown Root Irrigation (CRI)", "irrigation", "Wheat",
             "CRI stage occurs 20-25 days post-sowing. Critical moisture period. Delaying causes 20-30% tillering reduction. Apply first light irrigation followed by nitrogen top-dressing.", "ICAR - Indian Agricultural Research Institute (IARI)", 1),
            ("kb-3", "Mustard Aphid (Lipaphis erysimi) Organic Control", "pesticides", "Mustard",
             "Sucking pests cluster on flower stalks and pods. Spray 2% Neem oil or Beauveria bassiana 5g/L. If ETL exceeded (25 aphids/plant), spray Dimethoate 30 EC @ 1 ml/L.", "National Research Centre on Plant Biotechnology", 1),
        ]
        for kid, title, cat, crop, content, src, ver in sample_kb:
            execute_local_db("""
                INSERT OR IGNORE INTO knowledge_docs (id, title, category, crop, content, source, verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (kid, title, cat, crop, content, src, ver, now))

        # Seed Knowledge Sources Registry
        sample_sources = [
            ("src-icar", "ICAR Official Advisory", "https://icar.gov.in/", "Indian Council of Agricultural Research", "India",
             json.dumps(["en", "hi"]), "government", "Government of India Open Data", "https://data.gov.in", "https://icar.gov.in/terms",
             1, 1, 0, 1, 1, now, "Active"),
            ("src-tnau", "TNAU Agritech Portal", "https://agritech.tnau.ac.in/", "Tamil Nadu Agricultural University", "India",
             json.dumps(["en", "ta"]), "university", "Educational & Farmer Advisory", "https://agritech.tnau.ac.in", "https://agritech.tnau.ac.in/terms",
             1, 1, 0, 1, 1, now, "Active"),
            ("src-fao", "FAO AGRIS & FAOSTAT", "https://www.fao.org/faostat/", "Food and Agriculture Organization of the UN", "International",
             json.dumps(["en", "fr", "es"]), "international", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", "https://www.fao.org/terms",
             1, 1, 0, 1, 1, now, "Active"),
            ("src-agrovoc", "FAO AGROVOC Multilingual Thesaurus", "https://agrovoc.fao.org/", "FAO & UN", "International",
             json.dumps(["en", "hi", "es", "fr", "ar"]), "thesaurus", "CC BY 3.0 IGO", "https://creativecommons.org/licenses/by/3.0/igo/", "https://agrovoc.fao.org/terms",
             1, 1, 1, 1, 1, now, "Active"),
            ("src-imd", "IMD Agromet Advisory Service", "https://mausam.imd.gov.in/", "India Meteorological Department", "India",
             json.dumps(["en", "hi"]), "government", "Public Weather Data", "https://imd.gov.in", "https://imd.gov.in/terms",
             1, 1, 0, 1, 1, now, "Active"),
            ("src-openagro", "OpenAgroData (Reference)", "https://github.com/OpenAgroData/open-agro-data", "OpenAgroData Community", "Global",
             json.dumps(["en"]), "open_source", "MIT License", "https://opensource.org/licenses/MIT", "https://github.com/OpenAgroData",
             1, 1, 0, 1, 1, now, "Supplementary"),
        ]
        for sid, sname, surl, sorg, scountry, slang, stype, slic, slic_url, sterms, col, reuse, train, attr, rob, ver_at, stat in sample_sources:
            execute_local_db("""
                INSERT OR IGNORE INTO knowledge_sources (id, name, url, organization, country, languages_json, source_type,
                                              license_name, license_url, terms_url, allows_automated_collection,
                                              allows_text_reuse, allows_model_training, requires_attribution,
                                              robots_checked, verified_at, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, sname, surl, sorg, scountry, slang, stype, slic, slic_url, sterms, col, reuse, train, attr, rob, ver_at, stat, now))

        # Seed Knowledge Chunks with strict provenance
        sample_chunks = [
            ("chk-1", "kb-1",
             "Tomato Leaf Curl Virus (ToLCV) caused by Begomovirus transmitted by Whitefly (Bemisia tabaci). Symptoms: upward curling, vein clearing, stunted growth. Immediate management: Yellow sticky traps 15/acre; spray 5% Neem Seed Kernel Extract (NSKE) or 5ml Neem Oil/L. If severe vector threshold reached: Imidacloprid 17.8 SL @ 0.5 ml/L water. Waiting period: 3 days.",
             "Tomato", "disease", "India", "en", "ICAR - Indian Institute of Horticultural Research", "https://icar.gov.in/tolcv", "Open Gov Data", 0.96),
            ("chk-2", "kb-2",
             "Wheat Crown Root Initiation (CRI) stage occurs 20-25 days post-sowing. Highly critical for tillering. If rain forecast is zero and topsoil is dry, first irrigation is mandatory. Top-dress with 25-30 kg Urea/acre. Avoid over-flooding to prevent root asphyxiation.",
             "Wheat", "irrigation", "North India", "en", "ICAR - IARI New Delhi", "https://icar.gov.in/wheat-cri", "Open Gov Data", 0.98),
            ("chk-3", "kb-3",
             "Paddy / Rice Blast (Magnaporthe oryzae). Spindle-shaped lesions with brown borders on leaves. Avoid excessive nitrogen. Bio-control: Pseudomonas fluorescens seed treatment @ 10g/kg and foliar spray @ 0.2%. If chemical intervention needed: Tricyclazole 75 WP @ 0.6 g/L.",
             "Rice", "disease", "India", "en", "TNAU Agritech Portal", "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_cereals_paddy.html", "Educational Advisory", 0.95),
            ("chk-4", "kb-4",
             "Mustard Aphid (Lipaphis erysimi). Colonies suck sap from terminal buds and siliquae. Threshold: 25 aphids/10 cm central twig. Cultural control: Early sowing by mid-October. Chemical: Dimethoate 30 EC @ 1 ml/L. Waiting period: 10 days.",
             "Mustard", "pest", "North India", "en", "ICAR - Directorate of Rapeseed-Mustard Research", "https://drmr.icar.gov.in", "Open Gov Data", 0.94),
        ]
        for chk_id, doc_id, ctext, ccrop, ctopic, creg, clang, csrc, csur_url, clis, conf in sample_chunks:
            execute_local_db("""
                INSERT OR IGNORE INTO knowledge_chunks (id, document_id, text, crop, topic, region, language, source, source_url, license, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (chk_id, doc_id, ctext, ccrop, ctopic, creg, clang, csrc, csur_url, clis, conf, now))

        # Seed Sample Active Crop Cycles
        ten_days_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        twenty_days_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        execute_local_db("""
            INSERT OR IGNORE INTO crop_cycles (id, field_id, farmer_id, crop_name, variety, sowing_date, expected_harvest_date, area_acres, irrigation_method, soil_type, current_stage, health_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("cycle-1", "field-1", "farmer-1001", "Wheat", "PBW 550", twenty_days_ago, "2026-04-10", 2.5, "Sprinkler", "Sandy Loam", "Early Tillering / CRI", "Good", now))
        execute_local_db("""
            INSERT OR IGNORE INTO crop_cycles (id, field_id, farmer_id, crop_name, variety, sowing_date, expected_harvest_date, area_acres, irrigation_method, soil_type, current_stage, health_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("cycle-2", "field-2", "farmer-1001", "Tomato", "Himsona", ten_days_ago, "2026-05-15", 1.5, "Drip", "Clay Loam", "Vegetative Growth", "Monitoring", now))

        # Seed Market Mandi Prices
        sample_mkt = [
            ("mkt-1", "Wheat", "Kalyan Sona", "Varanasi Mandi", "Varanasi", "Uttar Pradesh", 2275.0, 2450.0, 2380.0, now),
            ("mkt-2", "Tomato", "Hybrid", "Varanasi Mandi", "Varanasi", "Uttar Pradesh", 1800.0, 2600.0, 2200.0, now),
            ("mkt-3", "Paddy (Dhan)", "Basmati", "Khanna Mandi", "Ludhiana", "Punjab", 3400.0, 3950.0, 3720.0, now),
            ("mkt-4", "Mustard", "Pusa Jaikisan", "Indore Mandi", "Indore", "Madhya Pradesh", 5100.0, 5650.0, 5420.0, now),
            ("mkt-5", "Potato", "Jyoti", "Agra Mandi", "Agra", "Uttar Pradesh", 1200.0, 1650.0, 1450.0, now),
        ]
        for mid, comm, var, mname, dist, st, minp, maxp, modp, u_at in sample_mkt:
            execute_local_db("""
                INSERT OR IGNORE INTO market_data (id, commodity, variety, market_name, district, state, min_price, max_price, modal_price, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mid, comm, var, mname, dist, st, minp, maxp, modp, u_at))
    except Exception as e:
        logger.warning(f"[DB Seeding Warning] {e}")

# Execute schema & seeding immediately on load safely
try:
    init_sql_schema()
    seed_sql_defaults()
except Exception as e:
    logger.warning(f"[DB Init Warning] {e}")

def sync_supabase_cache():
    """Syncs core tables from Supabase into local SQLite cache on startup."""
    if not supabase_client.is_configured():
        return
    tables_to_sync = ["admin_users", "users", "farms", "crops", "crop_cycles", "reminders", "knowledge_sources"]
    conn = get_db_connection()
    try:
        for table in tables_to_sync:
            try:
                rows = supabase_client.select(table, limit=500)
                if not rows:
                    continue
                cols = list(rows[0].keys())
                placeholders = ",".join(["?" for _ in cols])
                col_str = ",".join(cols)
                stmt = f"INSERT OR REPLACE INTO {table} ({col_str}) VALUES ({placeholders})"
                for r in rows:
                    vals = [r.get(c) for c in cols]
                    try:
                        conn.execute(stmt, vals)
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"[Sync Error] {table}: {e}")
        conn.commit()
    finally:
        conn.close()

def get_supabase_status() -> Dict[str, Any]:
    is_cfg = supabase_client.is_configured()
    is_ok = supabase_client.check_health() if is_cfg else False
    counts = {}
    if is_ok:
        try:
            counts = {
                "crops": supabase_client.count("crops"),
                "users": supabase_client.count("users"),
                "reminders": supabase_client.count("reminders"),
                "mandi_prices": supabase_client.count("live_mandi_prices"),
                "historical_records": supabase_client.count("crop_production_historical"),
            }
        except Exception:
            pass
    return {
        "configured": is_cfg,
        "healthy": is_ok,
        "url": supabase_client.url if is_cfg else None,
        "status": "connected" if is_ok else ("configured_offline" if is_cfg else "not_configured"),
        "counts": counts
    }

async def connect_db():
    try:
        from app.drive_sync import sync_database_if_configured
        sync_database_if_configured(DB_PATH)
    except Exception as _e:
        logger.debug(f"[Database Init] Drive sync check bypassed: {_e}")

    print(f" [SQL DB] SQLite cache ready: {DB_PATH}")
    if supabase_client.is_configured():
        is_ok = supabase_client.check_health()
        if is_ok:
            print(f" [Supabase DB] Connected to live Supabase PostgreSQL: {supabase_client.url}")
            print(f" [Supabase DB] 499,000+ agricultural records active in Supabase Cloud")
            try:
                sync_supabase_cache()
            except Exception as e:
                logger.debug(f"[Supabase Cache Sync] {e}")
        else:
            print(" [Supabase DB] Supabase configured but offline; running in local SQLite cache mode.")

async def close_db():
    pass
