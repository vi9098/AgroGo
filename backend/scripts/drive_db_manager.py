"""
AgriGo Google Drive Database Manager CLI.
Usage:
  python backend/scripts/drive_db_manager.py --help
  python backend/scripts/drive_db_manager.py --pull <DRIVE_LINK_OR_FILE_ID>
  python backend/scripts/drive_db_manager.py --verify
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.drive_sync import download_file_from_google_drive, extract_drive_file_id
from app.database import DB_PATH, get_db_connection

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="AgriGo Google Drive Cloud DB Sync Utility")
    parser.add_argument("--pull", type=str, help="Download & replace local SQLite database from Google Drive link/ID")
    parser.add_argument("--verify", action="store_true", help="Verify current local database health and row counts")
    args = parser.parse_args()

    print("=" * 65)
    print("      AgriGo Google Drive Cloud Database Manager")
    print("=" * 65)

    if args.pull:
        file_id = extract_drive_file_id(args.pull)
        print(f"[*] Target Google Drive File ID: {file_id}")
        print(f"[*] Local Destination Path:       {DB_PATH}")
        print("[*] Fetching database file directly from Google Drive...")
        
        success = download_file_from_google_drive(file_id, DB_PATH)
        if success:
            print("\n[SUCCESS] Database fetched from Google Drive and verified successfully!")
            args.verify = True
        else:
            print("\n[ERROR] Failed to fetch database from Google Drive.")
            print("Ensure the file on Google Drive has link sharing set to:")
            print("'Anyone with the link can view' (Viewer permission).")
            sys.exit(1)

    if args.verify or not sys.argv[1:]:
        if not os.path.exists(DB_PATH):
            print(f"[!] Database file does not exist locally at: {DB_PATH}")
            return
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        print(f"[*] Local Database Path: {DB_PATH}")
        print(f"[*] Database File Size:  {size_mb:.2f} MB")
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM users")
            user_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM crops")
            crop_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM crop_production_historical")
            hist_count = cur.fetchone()[0]
            conn.close()
            print(f"[OK] SQLite Connection:   Healthy (WAL Mode)")
            print(f"[OK] Active Farmers:      {user_count}")
            print(f"[OK] Active Crops:        {crop_count}")
            print(f"[OK] Historical Records:  {hist_count:,}")
        except Exception as e:
            print(f"[!] Database check failed: {e}")

if __name__ == "__main__":
    main()
