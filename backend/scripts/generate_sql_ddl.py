import os
import json
import sqlite3

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))
OUT_SQL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "supabase_schema.sql"))

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
tables = [r[0] for r in cursor.fetchall()]

from migrate_sqlite_to_supabase import build_create_table_sql

sql_statements = [
    "-- ============================================================================",
    "-- AgriGo Supabase PostgreSQL Schema Definition",
    "-- Project Host: db.lebkgjebavldqqflwwox.supabase.co:5432",
    "-- ============================================================================\n"
]

for t in tables:
    cursor.execute(f"PRAGMA table_info('{t}')")
    cols = [{"name": r[1], "type": r[2], "notnull": bool(r[3]), "default": r[4], "pk": bool(r[5])} for r in cursor.fetchall()]
    sql_statements.append(build_create_table_sql(t, cols))
    sql_statements.append("")

sql_statements.extend([
    "-- Performance Indexes",
    'CREATE INDEX IF NOT EXISTS idx_users_role ON "users"(role);',
    'CREATE INDEX IF NOT EXISTS idx_users_status ON "users"(status);',
    'CREATE INDEX IF NOT EXISTS idx_sessions_user ON "sessions"(user_id);',
    'CREATE INDEX IF NOT EXISTS idx_sessions_expires ON "sessions"(expires_at);',
    'CREATE INDEX IF NOT EXISTS idx_crops_farmer ON "crops"(farmer_id);',
    'CREATE INDEX IF NOT EXISTS idx_reminders_farmer ON "reminders"(farmer_id);',
    'CREATE INDEX IF NOT EXISTS idx_hist_crop_state ON "crop_production_historical"(crop_name, state_name);',
    'CREATE INDEX IF NOT EXISTS idx_hist_year ON "crop_production_historical"(year);',
    'CREATE INDEX IF NOT EXISTS idx_mandi_commodity ON "live_mandi_prices"(commodity);'
])

with open(OUT_SQL, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_statements))

conn.close()
print(f"Generated {OUT_SQL} with {len(tables)} tables and indexes.")
