import sys
import os

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from starlette.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.supabase_client import supabase_client
from app.database import get_supabase_status

client = TestClient(app)

def run_tests():
    print("=" * 65)
    print("      AgriGo Supabase Live Integration & CSP Verification")
    print("=" * 65)

    # Test 1: CSP and Permissions-Policy Headers
    res = client.get("/farmer.html")
    csp = res.headers.get("Content-Security-Policy", "")
    pp = res.headers.get("Permissions-Policy", "")
    
    print("\n1. Testing Security Headers on /farmer.html:")
    assert "https://unpkg.com" in csp, f"FAIL: unpkg.com missing from CSP: {csp}"
    assert "https://server.arcgisonline.com" in csp, f"FAIL: server.arcgisonline.com missing from CSP: {csp}"
    assert "https://*.supabase.co" in csp, f"FAIL: Supabase domain missing from CSP: {csp}"
    print("   [PASS] Content-Security-Policy allows unpkg.com, ArcGIS satellite tiles, and Supabase!")
    
    assert "run-ad-auction" not in pp, f"FAIL: run-ad-auction present in Permissions-Policy: {pp}"
    assert "geolocation=(self)" in pp, f"FAIL: standard geolocation missing from Permissions-Policy: {pp}"
    print(f"   [PASS] Clean Permissions-Policy: {pp}")

    # Test 2: Supabase Client Connectivity
    print("\n2. Testing Supabase Health & Connection:")
    status = get_supabase_status()
    print("   Status:", status)
    assert status.get("healthy") is True, f"FAIL: Supabase health check failed: {status}"
    assert status.get("status") == "connected", f"FAIL: Status not connected: {status}"
    print("   [PASS] Live Supabase PostgreSQL connected successfully!")

    # Test 3: Supabase Status API Endpoint
    print("\n3. Testing /api/v1/supabase/status Endpoint:")
    res_api = client.get("/api/v1/supabase/status")
    assert res_api.status_code == 200, f"FAIL: /api/v1/supabase/status returned {res_api.status_code}"
    api_data = res_api.json()
    assert api_data.get("healthy") is True
    print(f"   [PASS] API returned status 200: counts = {api_data.get('counts')}")

    # Test 4: Live Data Fetching through Supabase
    print("\n4. Testing Direct Supabase Table Queries:")
    crops = supabase_client.select("crops", limit=5)
    assert len(crops) > 0, "FAIL: No crops returned from Supabase"
    print(f"   [PASS] Fetched {len(crops)} crops from Supabase: {[c.get('crop_name') for c in crops]}")

    users = supabase_client.select("users", limit=3)
    assert len(users) > 0, "FAIL: No users returned from Supabase"
    print(f"   [PASS] Fetched {len(users)} users from Supabase: {[u.get('name') for u in users]}")

    reminders = supabase_client.select("reminders", limit=5)
    assert len(reminders) > 0, "FAIL: No reminders returned from Supabase"
    print(f"   [PASS] Fetched {len(reminders)} reminders from Supabase")

    historical = supabase_client.count("crop_production_historical")
    assert historical > 400000, f"FAIL: Expected > 400k historical rows, got {historical}"
    print(f"   [PASS] Verified {historical:,} historical crop records active in Supabase Cloud")

    print("\n" + "=" * 65)
    print("      ALL SUPABASE & CSP TESTS PASSED (100% VERIFIED)!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
