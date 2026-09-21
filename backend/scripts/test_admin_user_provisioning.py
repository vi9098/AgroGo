"""
Verification script for Admin User Provisioning and Redirection:
1. Verifies non-admin / unauthenticated users cannot access POST /api/admin/users (401/403)
2. Verifies an authenticated admin can provision another Administrator
3. Verifies the newly created admin can log in with their credentials and access admin APIs
4. Verifies an authenticated admin can provision a Farmer (with farms & crops auto-created)
5. Verifies duplicate identifier is rejected with 400
6. Verifies role filtering in GET /api/admin/users?role=admin & ?role=farmer
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from app.main import app
from app.database import query_one, execute_db
from app.services.session_service import SessionService, COOKIE_NAME

def run_tests():
    print("=" * 65, flush=True)
    print(" TESTING ADMIN USER PROVISIONING & REDIRECTION CONTROLS", flush=True)
    print("=" * 65, flush=True)

    client = TestClient(app, raise_server_exceptions=False)
    
    # 1. Unauthenticated request to POST /api/admin/users -> 401
    res1 = client.post("/api/admin/users", json={
        "name": "Unauthorized Attempt",
        "identifier": "unauth@example.com",
        "password": "Password123",
        "role": "admin"
    })
    assert res1.status_code == 401, f"Expected 401, got {res1.status_code}"
    print("[PASS] 1. Unauthenticated request to POST /api/admin/users rejected with 401", flush=True)

    # 2. Farmer request to POST /api/admin/users -> 403 Forbidden
    farmer_sess = SessionService.create_session("farmer-1001", "farmer")
    res2 = client.post(
        "/api/admin/users",
        json={
            "name": "Farmer Attempt",
            "identifier": "farmer.attempt@example.com",
            "password": "Password123",
            "role": "admin"
        },
        cookies={COOKIE_NAME: farmer_sess["session_id"]}
    )
    assert res2.status_code == 403, f"Expected 403, got {res2.status_code}"
    print("[PASS] 2. Farmer user attempting to create admin rejected with 403 Forbidden", flush=True)

    # 3. Authenticated Admin Login
    login_res = client.post("/api/auth/login", json={
        "identifier": "admin@legislative.com",
        "password": "Legislative@admin",
        "role": "admin"
    })
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    admin_sid = login_res.cookies.get(COOKIE_NAME)
    assert admin_sid, "Admin session cookie not returned"
    admin_cookies = {COOKIE_NAME: admin_sid}
    print("[PASS] 3. Primary Admin logged in successfully with server session", flush=True)

    # 4. Admin creates another Admin
    new_admin_email = "vikram.admin@agrigo.com"
    execute_db("DELETE FROM users WHERE phone = ?", (new_admin_email,))
    execute_db("DELETE FROM admin_users WHERE email = ?", (new_admin_email,))
    
    create_admin_res = client.post(
        "/api/admin/users",
        json={
            "name": "विक्रम सिंह (Co-Admin)",
            "identifier": new_admin_email,
            "password": "CoAdminPassword@2026",
            "role": "admin",
            "status": "active"
        },
        cookies=admin_cookies
    )
    assert create_admin_res.status_code == 200, f"Create admin failed: {create_admin_res.text}"
    admin_data = create_admin_res.json()
    assert admin_data["success"] is True
    created_admin_id = admin_data["user"]["id"]
    assert created_admin_id.startswith("admin-")
    print(f"[PASS] 4. Admin provisioned another Administrator: {admin_data['user']['name']} ({created_admin_id})", flush=True)

    # 5. Verify the newly created Admin can log in
    new_admin_login = client.post("/api/auth/login", json={
        "identifier": new_admin_email,
        "password": "CoAdminPassword@2026",
        "role": "admin"
    })
    assert new_admin_login.status_code == 200, f"New admin login failed: {new_admin_login.text}"
    new_admin_sid = new_admin_login.cookies.get(COOKIE_NAME)
    assert new_admin_sid, "New admin session cookie not set"
    
    # Verify new admin can access admin dashboard
    dash_res = client.get("/api/admin/dashboard", cookies={COOKIE_NAME: new_admin_sid})
    assert dash_res.status_code == 200, f"New admin dashboard failed: {dash_res.text}"
    print(f"[PASS] 5. Newly created Admin logged in and successfully accessed Admin Dashboard", flush=True)

    # 6. Admin creates a Farmer user
    new_farmer_phone = "9876500055"
    execute_db("DELETE FROM users WHERE phone = ?", (new_farmer_phone,))

    create_farmer_res = client.post(
        "/api/admin/users",
        json={
            "name": "सुरेश कुमार (Admin Added Farmer)",
            "identifier": new_farmer_phone,
            "password": "FarmerPassword@2026",
            "role": "farmer",
            "status": "active",
            "state": "पंजाब (Punjab)",
            "district": "लुधियाना (Ludhiana)",
            "farm_area": 5.0,
            "primary_crop": "धान / चावल (Paddy/Rice)"
        },
        cookies=admin_cookies
    )
    assert create_farmer_res.status_code == 200, f"Create farmer failed: {create_farmer_res.text}"
    farmer_data = create_farmer_res.json()
    assert farmer_data["success"] is True
    created_farmer_id = farmer_data["user"]["id"]
    assert created_farmer_id.startswith("farmer-")
    
    # Verify farm & crop in database
    db_farm = query_one("SELECT * FROM farms WHERE farmer_id = ?", (created_farmer_id,))
    assert db_farm is not None and db_farm["total_area_acres"] == 5.0
    db_crop = query_one("SELECT * FROM crops WHERE farmer_id = ?", (created_farmer_id,))
    assert db_crop is not None and "धान" in db_crop["crop_name"]
    print(f"[PASS] 6. Admin provisioned Farmer with auto-generated Farm ({db_farm['total_area_acres']} Ac) and Crop ({db_crop['crop_name']})", flush=True)

    # 7. Duplicate identifier is rejected with 400
    dup_res = client.post(
        "/api/admin/users",
        json={
            "name": "Duplicate User",
            "identifier": new_admin_email,
            "password": "AnotherPassword@2026",
            "role": "admin"
        },
        cookies=admin_cookies
    )
    assert dup_res.status_code == 400, f"Expected 400 for duplicate, got {dup_res.status_code}"
    print("[PASS] 7. Duplicate identifier rejected with 400 Bad Request", flush=True)

    # 8. Role filtering in GET /api/admin/users
    admins_only_res = client.get("/api/admin/users?role=admin", cookies=admin_cookies)
    assert admins_only_res.status_code == 200
    admins_list = admins_only_res.json()
    assert len(admins_list) >= 2, f"Expected at least 2 admins, got {len(admins_list)}: {admins_list}"
    assert all(u["role"] == "admin" for u in admins_list)

    farmers_only_res = client.get("/api/admin/users?role=farmer", cookies=admin_cookies)
    assert farmers_only_res.status_code == 200
    farmers_list = farmers_only_res.json()
    assert len(farmers_list) >= 1, f"Expected at least 1 farmer, got {len(farmers_list)}"
    assert all(u["role"] == "farmer" for u in farmers_list)
    print(f"[PASS] 8. Role filtering verified (Admins: {len(admins_list)}, Farmers: {len(farmers_list)})", flush=True)

    print("=" * 65, flush=True)
    print(" ALL ADMIN USER PROVISIONING & REDIRECTION TESTS PASSED!", flush=True)
    print("=" * 65, flush=True)

if __name__ == "__main__":
    run_tests()
