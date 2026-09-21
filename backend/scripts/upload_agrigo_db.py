import os
import sys
import time
import requests

SECRET_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
PROJECT_URL = os.environ.get("SUPABASE_URL", "https://lebkgjebavldqqflwwox.supabase.co")
BUCKET_NAME = "database"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))

headers = {
    "apikey": SECRET_KEY,
    "Authorization": f"Bearer {SECRET_KEY}"
}

print("=" * 70)
print("      AgriGo Supabase Cloud Database Uploader")
print("=" * 70)
file_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
print(f"[*] Local Database: {DB_PATH}")
print(f"[*] File Size:      {file_size_mb:.2f} MB")
print(f"[*] Supabase Host:  {PROJECT_URL}")
print(f"[*] Target Bucket:  {BUCKET_NAME}")
print("=" * 70)

# Step 1: Ensure bucket exists
print("[1/3] Checking / creating storage bucket...")
bucket_url = f"{PROJECT_URL}/storage/v1/bucket"

r_list = requests.get(bucket_url, headers=headers)
print("Existing buckets:", r_list.json() if r_list.status_code == 200 else r_list.text)

bucket_names = [b["name"] for b in r_list.json()] if r_list.status_code == 200 and isinstance(r_list.json(), list) else []

if BUCKET_NAME not in bucket_names:
    print(f"[*] Creating public bucket '{BUCKET_NAME}'...")
    create_payload = {
        "name": BUCKET_NAME,
        "id": BUCKET_NAME,
        "public": True,
        "file_size_limit": 524288000 # 500MB
    }
    r_create = requests.post(
        bucket_url,
        headers={**headers, "Content-Type": "application/json"},
        json=create_payload
    )
    print(f"[*] Create bucket response ({r_create.status_code}): {r_create.text}")
else:
    print(f"[OK] Bucket '{BUCKET_NAME}' already exists.")

# Step 2: Upload agrigo.db (91MB) with stream
upload_url = f"{PROJECT_URL}/storage/v1/object/{BUCKET_NAME}/agrigo.db"
upload_headers = {
    "apikey": SECRET_KEY,
    "Authorization": f"Bearer {SECRET_KEY}",
    "Content-Type": "application/x-sqlite3",
    "x-upsert": "true"
}

print(f"\n[2/3] Uploading agrigo.db ({file_size_mb:.2f} MB) to Supabase Storage...")
t_start = time.time()

with open(DB_PATH, "rb") as f:
    r_upload = requests.post(
        upload_url,
        headers=upload_headers,
        data=f,
        timeout=300
    )

elapsed = time.time() - t_start
print(f"[*] Upload HTTP Status: {r_upload.status_code}")
print(f"[*] Response Body: {r_upload.text}")

if r_upload.status_code in (200, 201):
    public_url = f"{PROJECT_URL}/storage/v1/object/public/{BUCKET_NAME}/agrigo.db"
    print(f"\n[3/3] [SUCCESS] Database uploaded successfully in {elapsed:.1f}s!")
    print("=" * 70)
    print(f"DIRECT PUBLIC SUPABASE DATABASE URL:\n{public_url}")
    print("=" * 70)

    # Verify download of header
    print("\n[*] Verifying remote database binary header...")
    v_res = requests.get(public_url, headers={"Range": "bytes=0-15"}, timeout=10)
    print("Header bytes received:", v_res.content)
    if v_res.content.startswith(b"SQLite format 3\x00"):
        print("[OK] Remote database header verified: Valid SQLite 3 Database!")
    else:
        print("[!] Note: Public URL might require public bucket policy or auth token.")
else:
    print(f"[ERROR] Upload failed: {r_upload.text}")
    sys.exit(1)
