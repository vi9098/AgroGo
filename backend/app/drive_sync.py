"""
AgriGo Google Drive Cloud Database Synchronization Engine.
Allows the backend to bootstrap and fetch the SQLite database directly from Google Drive
on server boot or cold start, enabling cloud deployments without giant Git files.
"""

import os
import re
import logging
import urllib.request
import urllib.parse
import http.cookiejar

logger = logging.getLogger("agrigo.drive_sync")

def extract_drive_file_id(url_or_id: str) -> str:
    """
    Extracts the Google Drive file ID from various Drive URL formats or returns raw ID.
    Examples:
      - https://drive.google.com/file/d/1A2B3C4D5E6F/view?usp=sharing -> 1A2B3C4D5E6F
      - https://drive.google.com/open?id=1A2B3C4D5E6F -> 1A2B3C4D5E6F
      - https://drive.google.com/uc?id=1A2B3C4D5E6F -> 1A2B3C4D5E6F
      - 1A2B3C4D5E6F -> 1A2B3C4D5E6F
    """
    cleaned = url_or_id.strip()
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', cleaned)
    if match:
        return match.group(1)
    match = re.search(r'id=([a-zA-Z0-9_-]+)', cleaned)
    if match:
        return match.group(1)
    return cleaned

def download_file_from_google_drive(file_id_or_url: str, destination_path: str) -> bool:
    """
    Downloads large files from Google Drive (handling virus scan confirmation for >25MB files).
    Verifies that the downloaded file is a valid SQLite 3 database.
    """
    file_id = extract_drive_file_id(file_id_or_url)
    if not file_id or len(file_id) < 10:
        logger.error(f"[Google Drive] Invalid Google Drive file ID or URL: '{file_id_or_url}'")
        return False

    temp_destination = f"{destination_path}.download.tmp"
    logger.info(f"[Google Drive] Initiating direct database download from Drive ID: {file_id}...")

    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AgriGo/2.0')
    ]

    base_url = "https://drive.google.com/uc?export=download"
    download_url = f"{base_url}&id={file_id}"

    try:
        req = urllib.request.Request(download_url)
        response = opener.open(req, timeout=45)
        content_type = response.headers.get("Content-Type", "")

        # If Google Drive prompts with a virus scan confirmation page (>25MB file)
        confirm_token = None
        for cookie in cookie_jar:
            if "download_warning" in cookie.name:
                confirm_token = cookie.value
                break

        if "text/html" in content_type and not confirm_token:
            html_text = response.read().decode("utf-8", errors="ignore")
            token_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', html_text)
            if token_match:
                confirm_token = token_match.group(1)
            else:
                # Direct usercontent link pattern
                uc_match = re.search(r'href="(/uc\?[^"]+confirm=[^"]+)"', html_text)
                if uc_match:
                    confirm_token = "t"

        if confirm_token:
            confirm_url = f"{download_url}&confirm={confirm_token}"
            logger.info(f"[Google Drive] Large file bypass confirmed, streaming data...")
            req = urllib.request.Request(confirm_url)
            response = opener.open(req, timeout=60)

        # Download stream to temporary file in chunks
        chunk_size = 1024 * 1024  # 1 MB chunk
        total_downloaded = 0
        os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)

        with open(temp_destination, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                total_downloaded += len(chunk)
                if total_downloaded % (10 * 1024 * 1024) == 0:
                    logger.info(f"[Google Drive] Downloaded {total_downloaded // (1024 * 1024)} MB...")

        # Verify SQLite header signature (first 16 bytes MUST be b'SQLite format 3\x00')
        with open(temp_destination, "rb") as f:
            header = f.read(16)
        if header != b'SQLite format 3\x00':
            logger.error(f"[Google Drive] Downloaded file is not a valid SQLite database (Header: {header[:16]}). Aborting sync.")
            if os.path.exists(temp_destination):
                os.remove(temp_destination)
            return False

        # Atomic move to final destination
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
            except Exception:
                pass
        os.replace(temp_destination, destination_path)
        logger.info(f"[Google Drive] Database successfully fetched and verified! Total size: {total_downloaded // (1024 * 1024)} MB.")
        return True

    except Exception as e:
        logger.error(f"[Google Drive] Failed to download database from Google Drive: {e}", exc_info=True)
        if os.path.exists(temp_destination):
            try:
                os.remove(temp_destination)
            except Exception:
                pass
        return False

def sync_database_if_configured(target_db_path: str) -> bool:
    """
    Checks if Google Drive DB configuration is set in environment, and downloads
    the database if missing locally or if forced.
    """
    drive_id = os.getenv("GOOGLE_DRIVE_DB_FILE_ID") or os.getenv("GOOGLE_DRIVE_DB_URL")
    if not drive_id:
        return False

    force_sync = os.getenv("FORCE_DRIVE_DB_SYNC", "false").lower() in ("1", "true", "yes")
    db_exists = os.path.exists(target_db_path) and os.path.getsize(target_db_path) > 1024

    if not db_exists or force_sync:
        logger.info(f"[Google Drive] Sync triggered. Local DB exists: {db_exists}, Force: {force_sync}.")
        return download_file_from_google_drive(drive_id, target_db_path)
    
    return False
