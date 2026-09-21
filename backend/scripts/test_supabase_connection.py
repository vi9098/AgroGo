import sys
import socket
import psycopg2

HOST = "db.lebkgjebavldqqflwwox.supabase.co"
PORT = 5432
DB = "postgres"
USER = "postgres"

print(f"[*] Testing network DNS & TCP connectivity to {HOST}:{PORT}...")
try:
    s = socket.create_connection((HOST, PORT), timeout=5)
    s.close()
    print("[OK] TCP connection to Supabase database host succeeded!")
except Exception as e:
    print(f"[!] TCP connection failed: {e}")

# Check password if provided in args or env
import os
password = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SUPABASE_DB_PASSWORD") or os.environ.get("PGPASSWORD")

if password:
    print(f"[*] Attempting PostgreSQL login with provided password...")
    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            dbname=DB,
            user=USER,
            password=password,
            connect_timeout=8
        )
        print("[SUCCESS] Connected to Supabase PostgreSQL database successfully!")
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        print(f"[*] PostgreSQL Version: {cursor.fetchone()[0]}")
        conn.close()
    except Exception as e:
        print(f"[!] PostgreSQL login failed: {e}")
else:
    print("[i] No password provided yet. PostgreSQL requires password authentication.")
