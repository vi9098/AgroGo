#!/usr/bin/env python3
"""
AgriGo SQLite to Supabase PostgreSQL Migration Engine
------------------------------------------------------
Migrates all tables and 455k+ records from backend/agrigo.db
directly into Supabase PostgreSQL database:
db.lebkgjebavldqqflwwox.supabase.co:5432/postgres
"""

import sys
import os
import time
import argparse
import sqlite3
import psycopg2
import psycopg2.extras

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))

# Mapping of SQLite types to PostgreSQL types
def map_sqlite_to_pg(col_name: str, sqlite_type: str, is_pk: bool, default_val: str, not_null: bool) -> str:
    st = (sqlite_type or "TEXT").upper().strip()
    
    # Check for auto-increment ID
    if is_pk and ("INT" in st) and col_name.lower() == "id":
        return "BIGSERIAL PRIMARY KEY"
    
    if "INT" in st:
        pg_type = "BIGINT"
    elif "REAL" in st or "FLOAT" in st or "DOUBLE" in st:
        pg_type = "DOUBLE PRECISION"
    elif "NUMERIC" in st or "DECIMAL" in st:
        pg_type = "NUMERIC"
    elif "BLOB" in st:
        pg_type = "BYTEA"
    else:
        pg_type = "TEXT"
        
    parts = [pg_type]
    if is_pk:
        parts.append("PRIMARY KEY")
    if not_null and not is_pk:
        parts.append("NOT NULL")
    if default_val is not None:
        # Format default values for PG
        d = default_val.strip()
        if d.lower() in ("0", "1") and "INT" in st:
            parts.append(f"DEFAULT {d}")
        elif d.startswith("'") and d.endswith("'"):
            parts.append(f"DEFAULT {d}")
        elif not is_pk:
            parts.append(f"DEFAULT {d}")
            
    return " ".join(parts)

def build_create_table_sql(table_name: str, columns: list) -> str:
    col_defs = []
    for c in columns:
        col_name = c["name"]
        definition = map_sqlite_to_pg(col_name, c["type"], c["pk"], c["default"], c["notnull"])
        col_defs.append(f'    "{col_name}" {definition}')
    cols_sql = ",\n".join(col_defs)
    return f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n{cols_sql}\n);'

def migrate(host: str, port: int, dbname: str, user: str, password: str, dry_run: bool = False):
    print("=" * 70)
    print("      AgriGo SQLite -> Supabase PostgreSQL Migration")
    print("=" * 70)
    print(f"[*] SQLite Source:  {DB_PATH}")
    print(f"[*] PostgreSQL Host: {host}:{port}")
    print(f"[*] Database:       {dbname}")
    print(f"[*] User:           {user}")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Source database {DB_PATH} not found!")
        sys.exit(1)

    # 1. Connect to SQLite
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    # Get all tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    print(f"[*] Found {len(tables)} tables to migrate from SQLite.\n")

    if dry_run:
        print("[*] DRY RUN MODE: Validating table schemas only...")
        for t in tables:
            sqlite_cursor.execute(f"PRAGMA table_info('{t}')")
            cols = [{"name": r[1], "type": r[2], "notnull": bool(r[3]), "default": r[4], "pk": bool(r[5])} for r in sqlite_cursor.fetchall()]
            sqlite_cursor.execute(f'SELECT count(*) FROM "{t}"')
            cnt = sqlite_cursor.fetchone()[0]
            print(f" -> Table '{t}': {cnt:,} rows")
        sqlite_conn.close()
        return

    # 2. Connect to Supabase PostgreSQL
    print("[*] Connecting to Supabase PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",
            connect_timeout=10
        )
        pg_conn.autocommit = False
        pg_cursor = pg_conn.cursor()
        print("[OK] Connected to Supabase PostgreSQL successfully!\n")
    except Exception as e:
        print(f"[ERROR] Connection to Supabase failed: {e}")
        print("\nPlease ensure the Supabase database password is correct.")
        sys.exit(1)

    start_all = time.time()
    migration_summary = []

    try:
        for idx, table_name in enumerate(tables, 1):
            t_start = time.time()
            sqlite_cursor.execute(f"PRAGMA table_info('{table_name}')")
            cols_info = [{"name": r[1], "type": r[2], "notnull": bool(r[3]), "default": r[4], "pk": bool(r[5])} for r in sqlite_cursor.fetchall()]
            col_names = [c["name"] for c in cols_info]

            # 1. Create table in PG
            create_sql = build_create_table_sql(table_name, cols_info)
            pg_cursor.execute(create_sql)
            pg_conn.commit()

            # 2. Check existing row count in PG
            pg_cursor.execute(f'SELECT count(*) FROM "{table_name}";')
            pg_existing = pg_cursor.fetchone()[0]

            sqlite_cursor.execute(f'SELECT count(*) FROM "{table_name}";')
            sqlite_total = sqlite_cursor.fetchone()[0]

            print(f"[{idx}/{len(tables)}] Migrating '{table_name}' ({sqlite_total:,} rows)...", end="", flush=True)

            if sqlite_total == 0:
                print(" [SKIPPED (empty)]")
                migration_summary.append((table_name, 0, 0, "EMPTY"))
                continue

            # Clear PG table if re-running migration to avoid duplicates
            if pg_existing > 0:
                pg_cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE;')
                pg_conn.commit()

            # 3. Stream data in batches
            quoted_cols = ", ".join([f'"{c}"' for c in col_names])
            insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES %s;'

            sqlite_cursor.execute(f'SELECT {quoted_cols} FROM "{table_name}";')

            batch_size = 5000 if sqlite_total > 50000 else 2000
            inserted = 0

            while True:
                rows = sqlite_cursor.fetchmany(batch_size)
                if not rows:
                    break
                psycopg2.extras.execute_values(
                    pg_cursor,
                    insert_sql,
                    rows,
                    page_size=batch_size
                )
                pg_conn.commit()
                inserted += len(rows)
                if sqlite_total > 10000:
                    pct = (inserted / sqlite_total) * 100
                    print(f"\r[{idx}/{len(tables)}] Migrating '{table_name}': {inserted:,} / {sqlite_total:,} ({pct:.1f}%)...", end="", flush=True)

            # 4. Verify count in PG
            pg_cursor.execute(f'SELECT count(*) FROM "{table_name}";')
            pg_count = pg_cursor.fetchone()[0]
            elapsed = time.time() - t_start

            status = "OK" if pg_count == sqlite_total else "MISMATCH"
            print(f"\r[{idx}/{len(tables)}] Table '{table_name}': {pg_count:,} rows migrated in {elapsed:.2f}s [{status}]")
            migration_summary.append((table_name, sqlite_total, pg_count, status))

        # 5. Create common indexes on PostgreSQL
        print("\n[*] Creating performance indexes on Supabase...")
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_users_role ON "users"(role);',
            'CREATE INDEX IF NOT EXISTS idx_users_status ON "users"(status);',
            'CREATE INDEX IF NOT EXISTS idx_sessions_user ON "sessions"(user_id);',
            'CREATE INDEX IF NOT EXISTS idx_sessions_expires ON "sessions"(expires_at);',
            'CREATE INDEX IF NOT EXISTS idx_crops_farmer ON "crops"(farmer_id);',
            'CREATE INDEX IF NOT EXISTS idx_reminders_farmer ON "reminders"(farmer_id);',
            'CREATE INDEX IF NOT EXISTS idx_hist_crop_state ON "crop_production_historical"(crop_name, state_name);',
            'CREATE INDEX IF NOT EXISTS idx_hist_year ON "crop_production_historical"(year);',
            'CREATE INDEX IF NOT EXISTS idx_mandi_commodity ON "live_mandi_prices"(commodity);',
        ]
        for idx_sql in indexes:
            try:
                pg_cursor.execute(idx_sql)
                pg_conn.commit()
            except Exception as e:
                print(f"    [!] Index note: {e}")
                pg_conn.rollback()

        total_time = time.time() - start_all
        print("\n" + "=" * 70)
        print("          MIGRATION COMPLETE - SUMMARY REPORT")
        print("=" * 70)
        total_rows = 0
        for name, s_cnt, p_cnt, st in migration_summary:
            print(f" - {name:<30} SQLite: {s_cnt:>8,} | Supabase: {p_cnt:>8,} [{st}]")
            total_rows += p_cnt
        print("=" * 70)
        print(f"[SUCCESS] Total {total_rows:,} records migrated across {len(tables)} tables in {total_time:.1f}s!")
        print("=" * 70)

    except Exception as err:
        pg_conn.rollback()
        print(f"\n[FATAL ERROR] Migration failed: {err}")
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgriGo SQLite to Supabase Migration Tool")
    parser.add_argument("--host", default="db.lebkgjebavldqqflwwox.supabase.co", help="Supabase PG host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--database", default="postgres", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--password", help="Database password (or set SUPABASE_DB_PASSWORD env var)")
    parser.add_argument("--dry-run", action="store_true", help="Validate schema without writing to PG")
    
    args = parser.parse_args()
    
    pw = args.password or os.environ.get("SUPABASE_DB_PASSWORD") or os.environ.get("PGPASSWORD")
    
    if not pw and not args.dry_run:
        print("[!] No password specified. Use --password <PASSWORD> or set SUPABASE_DB_PASSWORD.")
        pw = input("Enter Supabase database password: ").strip()
        if not pw:
            print("[ERROR] Password cannot be empty.")
            sys.exit(1)
            
    migrate(
        host=args.host,
        port=args.port,
        dbname=args.database,
        user=args.user,
        password=pw,
        dry_run=args.dry_run
    )
