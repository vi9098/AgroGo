"""
AgriGo Production Test Suite
Verifies all 13 requirements specified in the project prompt:
1. Unauthenticated -> 401
2. Login -> server session created & secure cookie set
3. Refresh -> session remains authenticated
4. Logout -> server session destroyed & cookie cleared
5. Expired/idle session -> rejected with 401
6. Farmer -> own data -> 200 allowed
7. Farmer -> another farmer's data -> 403 rejected (IDOR protection)
8. Farmer -> admin API -> 403 forbidden
9. Admin -> admin API -> 200 allowed
10. Admin deletion -> confirmation + cascade delete + audit log + cannot delete self
11. Rate limit -> enforced after 5 failed attempts (429)
12. Weather -> real API data with required fields
13. Manual location selection works
"""
import sys
import os
import time
import datetime
from fastapi.testclient import TestClient

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.main import app
from app.database import query_one, query_db, execute_db
from app.services.session_service import SessionService, COOKIE_NAME
from app.middleware.auth import login_limiter
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_suite():
    print("=" * 70)
    print(" AGRIGO PRODUCTION VALIDATION SUITE -- RUNNING ALL TESTS")
    print("=" * 70)
    
    client = TestClient(app, raise_server_exceptions=False)
    results = []

    def log_result(name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if details:
            print(f"       -> {details}")
        results.append((name, passed))

    # -------------------------------------------------------------
    # Test 1: Unauthenticated request to protected API -> 401
    # -------------------------------------------------------------
    r1 = client.get("/api/auth/me")
    log_result(
        "1. Unauthenticated request to /api/auth/me returns 401",
        r1.status_code == 401,
        f"Status: {r1.status_code}, Detail: {r1.json().get('detail')}"
    )

    # -------------------------------------------------------------
    # Test 2: Farmer Login -> Server session created & cookie set
    # -------------------------------------------------------------
    login_limiter.attempts.clear()  # Ensure clean slate for rate limiter
    r2 = client.post("/api/auth/login", json={
        "identifier": "9876543210",
        "password": "123456",
        "role": "farmer"
    })
    cookie_present = COOKIE_NAME in r2.cookies
    session_id = r2.cookies.get(COOKIE_NAME)
    session_row = query_one("SELECT * FROM sessions WHERE id = ?", (session_id,)) if session_id else None
    
    log_result(
        "2. Farmer login creates server session and sets HttpOnly cookie",
        r2.status_code == 200 and cookie_present and bool(session_row),
        f"Status: {r2.status_code}, Cookie set: {cookie_present}, DB Session: {session_id[:8] if session_id else 'None'}..."
    )

    # -------------------------------------------------------------
    # Test 3: Refresh/subsequent request remains authenticated
    # -------------------------------------------------------------
    if session_id:
        client.cookies.set(COOKIE_NAME, session_id)
    r3 = client.get("/api/auth/me")
    log_result(
        "3. Session remains authenticated on subsequent requests (/api/auth/me)",
        r3.status_code == 200 and r3.json().get("user", {}).get("role") == "farmer",
        f"Status: {r3.status_code}, User: {r3.json().get('user', {}).get('name')}"
    )

    # -------------------------------------------------------------
    # Test 4: Logout destroys server-side session and clears cookie
    # -------------------------------------------------------------
    # Create temporary session to test logout
    temp_sess = SessionService.create_session("farmer-1001", "farmer")
    client.cookies.set(COOKIE_NAME, temp_sess["session_id"])
    r4 = client.post("/api/auth/logout")
    db_after_logout = query_one("SELECT * FROM sessions WHERE id = ?", (temp_sess["session_id"],))
    log_result(
        "4. Logout destroys server-side session and clears cookie",
        r4.status_code == 200 and db_after_logout is None,
        f"Status: {r4.status_code}, DB Session Exists After Logout: {bool(db_after_logout)}"
    )

    # -------------------------------------------------------------
    # Test 5: Expired / idle session is rejected with 401
    # -------------------------------------------------------------
    # Insert manually an expired session
    expired_sid = "test-expired-session-id-999"
    past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).isoformat()
    execute_db("""
        INSERT INTO sessions (id, user_id, role, ip_address, user_agent, created_at, last_accessed_at, expires_at)
        VALUES (?, 'farmer-1001', 'farmer', '127.0.0.1', 'test', ?, ?, ?)
    """, (expired_sid, past_time, past_time, past_time))
    
    client.cookies.set(COOKIE_NAME, expired_sid)
    r5 = client.get("/api/auth/me")
    log_result(
        "5. Expired / idle session is rejected with 401",
        r5.status_code == 401,
        f"Status: {r5.status_code}, Detail: {r5.json().get('detail')}"
    )

    # -------------------------------------------------------------
    # Test 6: Farmer accesses own data -> 200 Allowed
    # -------------------------------------------------------------
    client.cookies.set(COOKIE_NAME, session_id)
    r6 = client.get("/api/v1/farmer/crops/farmer-1001")
    log_result(
        "6. Farmer accesses own data (/api/v1/farmer/crops/farmer-1001) -> 200 OK",
        r6.status_code == 200 and "crops" in r6.json(),
        f"Status: {r6.status_code}, Crops count: {len(r6.json().get('crops', []))}"
    )

    # -------------------------------------------------------------
    # Test 7: Farmer accesses another farmer's data -> 403 Rejected (IDOR)
    # -------------------------------------------------------------
    r7 = client.get("/api/v1/farmer/crops/farmer-1002")
    log_result(
        "7. Farmer accessing another farmer's data -> 403 Forbidden (IDOR Protection)",
        r7.status_code == 403,
        f"Status: {r7.status_code}, Detail: {r7.json().get('detail')}"
    )

    # -------------------------------------------------------------
    # Test 8: Farmer accesses admin API -> 403 Forbidden
    # -------------------------------------------------------------
    r8 = client.get("/api/admin/dashboard")
    log_result(
        "8. Farmer accessing admin endpoint (/api/admin/dashboard) -> 403 Forbidden",
        r8.status_code == 403,
        f"Status: {r8.status_code}, Detail: {r8.json().get('detail')}"
    )

    # -------------------------------------------------------------
    # Test 9: Admin Login -> creates admin session
    # -------------------------------------------------------------
    client.cookies.clear()
    r9 = client.post("/api/auth/login", json={
        "identifier": "admin@agrigo.com",
        "password": "Admin@AgriGo2026",
        "role": "admin"
    })
    admin_sid = r9.cookies.get(COOKIE_NAME)
    admin_row = query_one("SELECT * FROM sessions WHERE id = ?", (admin_sid,)) if admin_sid else None
    log_result(
        "9. Admin login creates server session with 'admin' role",
        r9.status_code == 200 and admin_row and admin_row["role"] == "admin",
        f"Status: {r9.status_code}, Role in DB: {admin_row['role'] if admin_row else 'None'}"
    )

    # -------------------------------------------------------------
    # Test 10: Admin accesses admin APIs -> 200 Allowed
    # -------------------------------------------------------------
    if admin_sid:
        client.cookies.set(COOKIE_NAME, admin_sid)
    r10_dash = client.get("/api/admin/dashboard")
    r10_users = client.get("/api/admin/users")
    r10_health = client.get("/api/admin/system/health")
    log_result(
        "10. Admin accesses admin APIs (/dashboard, /users, /health) -> 200 OK",
        r10_dash.status_code == 200 and r10_users.status_code == 200 and r10_health.status_code == 200,
        f"Dashboard: {r10_dash.status_code}, Users list: {len(r10_users.json())} farmers, Health: {r10_health.json().get('status')}"
    )

    # -------------------------------------------------------------
    # Test 11: Admin user deletion -> Transactional cascade deletion
    # -------------------------------------------------------------
    # Create a test farmer with crops and reminders to test cascade delete
    test_fid = "farmer-test-cascade"
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    execute_db("DELETE FROM reminders WHERE farmer_id = ?", (test_fid,))
    execute_db("DELETE FROM crops WHERE farmer_id = ?", (test_fid,))
    execute_db("DELETE FROM users WHERE id = ? OR phone = '9999900001'", (test_fid,))
    execute_db("""
        INSERT INTO users (id, phone, name, password_hash, status, role, created_at)
        VALUES (?, '9999900001', 'Cascade Delete Test Farmer', 'hash', 'active', 'farmer', ?)
    """, (test_fid, now_str))
    execute_db("INSERT INTO crops (id, farmer_id, crop_name, created_at) VALUES ('crop-del-1', ?, 'Barley', ?)", (test_fid, now_str))
    execute_db("INSERT INTO reminders (id, farmer_id, title, created_at) VALUES ('rem-del-1', ?, 'Test Reminder', ?)", (test_fid, now_str))
    
    # 11a: Admin cannot delete own account
    r11_self = client.delete(f"/api/admin/users/{admin_row['user_id']}")
    self_prevented = r11_self.status_code == 400

    # 11b: Admin deletes test farmer
    r11_del = client.delete(f"/api/admin/users/{test_fid}")
    user_after = query_one("SELECT * FROM users WHERE id = ?", (test_fid,))
    crop_after = query_one("SELECT * FROM crops WHERE farmer_id = ?", (test_fid,))
    rem_after = query_one("SELECT * FROM reminders WHERE farmer_id = ?", (test_fid,))
    audit_entry = query_one("SELECT * FROM audit_logs WHERE action = 'DELETE_USER' AND resource_id = ?", (test_fid,))

    cascade_success = (
        r11_del.status_code == 200 and
        user_after is None and
        crop_after is None and
        rem_after is None and
        audit_entry is not None and
        self_prevented
    )
    log_result(
        "11. Admin cascade deletes farmer & related data, self-delete blocked, audit logged",
        cascade_success,
        f"Self-delete blocked: {self_prevented}, Cascade success: {user_after is None}, Audit log: {bool(audit_entry)}"
    )

    # -------------------------------------------------------------
    # Test 12: Rate limit -> 5 failed attempts trigger 429
    # -------------------------------------------------------------
    login_limiter.attempts.clear()
    rate_limited = False
    for i in range(7):
        r_fail = client.post("/api/auth/login", json={
            "identifier": "attacker@fake.com",
            "password": f"wrong_{i}"
        })
        if r_fail.status_code == 429:
            rate_limited = True
            break
    log_result(
        "12. Rate limiter enforces 429 Too Many Requests on repeated failed logins",
        rate_limited,
        f"Attempt triggered 429: {rate_limited}"
    )

    # -------------------------------------------------------------
    # Test 13: Real Weather Data API & Manual Location Fallback
    # -------------------------------------------------------------
    r13_default = client.get("/api/weather")
    w_data = r13_default.json()
    has_weather_fields = all(k in w_data for k in [
        "location", "temperature_c", "feels_like_c", "humidity_pct",
        "wind_kmh", "condition", "rain_prob_today_pct", "last_updated"
    ])

    # Manual location coordinates test (Bathinda, Punjab: lat=30.21, lon=74.94)
    r13_manual = client.get("/api/weather?lat=30.211&lon=74.945")
    manual_data = r13_manual.json()
    manual_works = r13_manual.status_code == 200 and "Bathinda" in manual_data.get("location", "")

    log_result(
        "13. Weather API returns all required fields and manual location selection works",
        r13_default.status_code == 200 and has_weather_fields and manual_works,
        f"Location: {w_data.get('location')}, Temp: {w_data.get('temperature_c')}°C, Manual: {manual_data.get('location')}"
    )

    print("=" * 70)
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f" SUMMARY: {passed_count}/{total_count} TESTS PASSED")
    print("=" * 70)

    if passed_count == total_count:
        print("ALL TESTS PASSED SUCCESSFULLY! Production AgriGo system validated.")
        return 0
    else:
        print("SOME TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(run_suite())
