import requests
import json
import os

API_KEY = os.environ.get("SUPABASE_KEY", "")
PROJECT_URL = os.environ.get("SUPABASE_URL", "https://lebkgjebavldqqflwwox.supabase.co")
BUCKET_NAME = "database"

headers = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print(f"[*] Checking/Creating bucket '{BUCKET_NAME}'...")
res = requests.post(
    f"{PROJECT_URL}/storage/v1/bucket",
    headers=headers,
    json={"name": BUCKET_NAME, "id": BUCKET_NAME, "public": True}
)

print("Create Bucket Status:", res.status_code)
print("Create Bucket Body:", res.text)

# List buckets
r_list = requests.get(f"{PROJECT_URL}/storage/v1/bucket", headers=headers)
print("Buckets currently available:", r_list.text)
