import os
import requests

SECRET_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
PROJECT_URL = os.environ.get("SUPABASE_URL", "https://lebkgjebavldqqflwwox.supabase.co")

headers = {
    "apikey": SECRET_KEY,
    "Authorization": f"Bearer {SECRET_KEY}",
    "Range-Unit": "items",
    "Prefer": "count=exact"
}

tables = [
    "admin_users", "users", "farms", "crops", "conversations", "messages", 
    "otps", "sessions", "reminders", "audit_logs", "knowledge_docs",
    "knowledge_sources", "knowledge_chunks", "live_mandi_prices", 
    "crop_production_historical", "district_crop_benchmarks", "crop_cycles",
    "farmer_observations", "fields", "market_data", "soil_data", "weather_cache"
]

print("=" * 65)
print("      Supabase PostgreSQL Live Table Row Counts")
print("=" * 65)

total_records = 0

for t in tables:
    try:
        r = requests.get(f"{PROJECT_URL}/rest/v1/{t}?select=*", headers={**headers, "Range": "0-0"}, timeout=10)
        # Content-Range header has format: 0-0/total or */total
        content_range = r.headers.get("Content-Range", "")
        if "/" in content_range:
            count = int(content_range.split("/")[1])
        else:
            count = len(r.json()) if isinstance(r.json(), list) else 0
        print(f" - {t:<30}: {count:>8,} rows")
        total_records += count
    except Exception as e:
        print(f" - {t:<30}: Error ({e})")

print("=" * 65)
print(f"TOTAL RECORDS IN SUPABASE: {total_records:,}")
print("=" * 65)
