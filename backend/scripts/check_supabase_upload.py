import os
import requests

SECRET_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
PROJECT_URL = os.environ.get("SUPABASE_URL", "https://lebkgjebavldqqflwwox.supabase.co")

headers = {
    "apikey": SECRET_KEY,
    "Authorization": f"Bearer {SECRET_KEY}"
}

print("=" * 60)
print("[*] Checking Supabase Storage Buckets...")
print("=" * 60)
r_buckets = requests.get(f"{PROJECT_URL}/storage/v1/bucket", headers=headers)
print("Status:", r_buckets.status_code)
buckets = r_buckets.json() if r_buckets.status_code == 200 else []
print("Buckets found:", buckets)

for b in buckets:
    b_name = b["name"] if isinstance(b, dict) else str(b)
    print(f"\n[*] Files in bucket '{b_name}':")
    r_files = requests.post(
        f"{PROJECT_URL}/storage/v1/object/list/{b_name}",
        headers={**headers, "Content-Type": "application/json"},
        json={"limit": 100, "offset": 0}
    )
    print("Files:", r_files.text)

print("\n" + "=" * 60)
print("[*] Checking Supabase Database Tables (PostgreSQL)...")
print("=" * 60)
r_meta = requests.get(f"{PROJECT_URL}/rest/v1/", headers=headers)
if r_meta.status_code == 200:
    definitions = r_meta.json().get("definitions", {})
    print(f"Total Tables in PostgreSQL: {len(definitions)}")
    for t in list(definitions.keys())[:25]:
        print(f" - {t}")
else:
    print("REST Tables status:", r_meta.status_code, r_meta.text)
