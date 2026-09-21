#!/usr/bin/env python3
"""
AgriGo Supabase Storage S3 / REST Database Uploader
---------------------------------------------------
Uploads agrigo.db (91MB) directly to Supabase Storage:
Endpoint: https://lebkgjebavldqqflwwox.storage.supabase.co/storage/v1/s3
or via Supabase REST Storage API.
"""

import sys
import os
import argparse
import time

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agrigo.db"))

def upload_via_s3(endpoint_url: str, access_key: str, secret_key: str, bucket_name: str, region: str = "us-east-1"):
    import boto3
    from botocore.client import Config

    print("=" * 70)
    print("       Supabase S3 Storage Database Upload")
    print("=" * 70)
    print(f"[*] Local File:      {DB_PATH} ({os.path.getsize(DB_PATH) / (1024*1024):.2f} MB)")
    print(f"[*] S3 Endpoint:     {endpoint_url}")
    print(f"[*] Target Bucket:   {bucket_name}")
    print("=" * 70)

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version='s3v4')
    )

    # Check or create bucket
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"[OK] Bucket '{bucket_name}' exists and is accessible.")
    except Exception as e:
        print(f"[*] Creating bucket '{bucket_name}'...")
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            print(f"[OK] Bucket '{bucket_name}' created successfully.")
        except Exception as ce:
            print(f"[!] Bucket access note: {ce}")

    # Upload with progress
    file_size = os.path.getsize(DB_PATH)
    start_time = time.time()
    uploaded_bytes = 0

    def progress_callback(bytes_amount):
        nonlocal uploaded_bytes
        uploaded_bytes += bytes_amount
        percent = (uploaded_bytes / file_size) * 100
        mb = uploaded_bytes / (1024 * 1024)
        total_mb = file_size / (1024 * 1024)
        print(f"\r[*] Uploading agrigo.db: {mb:.2f}MB / {total_mb:.2f}MB ({percent:.1f}%)...", end="", flush=True)

    print("[*] Starting upload...")
    try:
        s3_client.upload_file(
            DB_PATH,
            bucket_name,
            "agrigo.db",
            Callback=progress_callback
        )
        elapsed = time.time() - start_time
        print(f"\n[SUCCESS] agrigo.db uploaded to '{bucket_name}/agrigo.db' in {elapsed:.1f}s!")
        print(f"[*] Public/Direct S3 URI: {endpoint_url}/{bucket_name}/agrigo.db")
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        sys.exit(1)

def upload_via_rest(project_url: str, api_key: str, bucket_name: str):
    import requests

    print("=" * 70)
    print("       Supabase REST Storage Database Upload")
    print("=" * 70)
    print(f"[*] Local File:      {DB_PATH} ({os.path.getsize(DB_PATH) / (1024*1024):.2f} MB)")
    print(f"[*] Project URL:     {project_url}")
    print(f"[*] Target Bucket:   {bucket_name}")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "apikey": api_key
    }

    # 1. Ensure bucket exists
    bucket_url = f"{project_url}/storage/v1/bucket"
    try:
        r = requests.get(bucket_url, headers=headers, timeout=10)
        if r.status_code == 200:
            buckets = [b["name"] for b in r.json()]
            if bucket_name not in buckets:
                print(f"[*] Creating public bucket '{bucket_name}'...")
                create_res = requests.post(
                    bucket_url,
                    headers=headers,
                    json={"name": bucket_name, "id": bucket_name, "public": True},
                    timeout=10
                )
                if create_res.status_code in (200, 201):
                    print(f"[OK] Bucket '{bucket_name}' created.")
                else:
                    print(f"[!] Create bucket notice: {create_res.text}")
            else:
                print(f"[OK] Bucket '{bucket_name}' exists.")
    except Exception as e:
        print(f"[!] Bucket check note: {e}")

    # 2. Upload file
    upload_url = f"{project_url}/storage/v1/object/{bucket_name}/agrigo.db"
    upload_headers = {
        "Authorization": f"Bearer {api_key}",
        "apikey": api_key,
        "Content-Type": "application/octet-stream",
        "x-upsert": "true"
    }

    print("[*] Uploading agrigo.db (91MB) to Supabase Storage...")
    start_time = time.time()
    try:
        with open(DB_PATH, "rb") as f:
            res = requests.post(upload_url, headers=upload_headers, data=f, timeout=120)
        if res.status_code in (200, 201):
            elapsed = time.time() - start_time
            print(f"[SUCCESS] agrigo.db uploaded successfully in {elapsed:.1f}s!")
            public_url = f"{project_url}/storage/v1/object/public/{bucket_name}/agrigo.db"
            print(f"[*] Direct Public URL: {public_url}")
        else:
            print(f"[ERROR] Upload failed with status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload AgriGo DB to Supabase Storage")
    parser.add_argument("--s3-endpoint", default="https://lebkgjebavldqqflwwox.storage.supabase.co/storage/v1/s3", help="Supabase S3 endpoint")
    parser.add_argument("--access-key", help="Supabase S3 Access Key ID")
    parser.add_argument("--secret-key", help="Supabase S3 Secret Access Key")
    parser.add_argument("--api-key", help="Supabase anon or service_role key")
    parser.add_argument("--project-url", default="https://lebkgjebavldqqflwwox.supabase.co", help="Supabase Project URL")
    parser.add_argument("--bucket", default="database", help="Target bucket name")

    args = parser.parse_args()

    access_key = args.access_key or os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("SUPABASE_S3_ACCESS_KEY")
    secret_key = args.secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get("SUPABASE_S3_SECRET_KEY")
    api_key = args.api_key or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if access_key and secret_key:
        upload_via_s3(args.s3_endpoint, access_key, secret_key, args.bucket)
    elif api_key:
        upload_via_rest(args.project_url, api_key, args.bucket)
    else:
        print("[!] Missing credentials for upload.")
        print("Please provide EITHER:")
        print("  1) S3 credentials:   --access-key <KEY> --secret-key <SECRET>")
        print("  2) Supabase API key: --api-key <ANON_OR_SERVICE_ROLE_KEY>")
        print("Target endpoint: " + args.s3_endpoint)
