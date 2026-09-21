"""
Verification script for:
1. Public Farmer Registration with Farm Details, State, District, and Area
2. Automatic Farm & Crop record generation in database
3. Session cookie issuance upon registration
4. Prevention of duplicate phone registration
5. Weather API testing for dynamic state/district selection
"""
import sys
import os
import asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.main import app
from app.database import query_one, execute_db

async def run_tests():
    print("=" * 65)
    print(" TESTING FARMER REGISTRATION PORTAL & WEATHER SELECTION")
    print("=" * 65)

    test_phone = "+919876543999"
    # Clean up test user if previously exists
    existing = query_one("SELECT id FROM users WHERE phone = ?", (test_phone,))
    if existing:
        execute_db("DELETE FROM crops WHERE farmer_id = ?", (existing["id"],))
        execute_db("DELETE FROM farms WHERE farmer_id = ?", (existing["id"],))
        execute_db("DELETE FROM users WHERE id = ?", (existing["id"],))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Register new farmer
        reg_payload = {
            "name": "विक्रम सिंह (Vikram Singh)",
            "phone": test_phone,
            "password": "StrongPassword@2026",
            "state": "पंजाब (Punjab)",
            "district": "बठिंडा (Bathinda)",
            "village": "तलवंडी साबो",
            "farm_area": 4.5,
            "primary_crop": "गेहूं (Wheat)",
            "soil_type": "दोमट मिट्टी (Loamy Soil)",
            "irrigation_type": "ट्यूबवेल / सबमर्सिबल (Borewell)",
            "preferred_language": "hi"
        }

        res = await client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 200, f"Registration failed: {res.text}"
        data = res.json()
        assert data["success"] is True
        user = data["user"]
        farmer_id = user["id"]
        assert user["role"] == "farmer"
        assert user["farm_area"] == 4.5
        assert "agrigo_session" in res.cookies, "Registration must set session cookie"
        print(f"[PASS] 1. Registration endpoint successful. Created Farmer: {user['name']} ({farmer_id})")

        # 2. Verify User Record in DB
        db_user = query_one("SELECT * FROM users WHERE id = ?", (farmer_id,))
        assert db_user is not None
        assert db_user["role"] == "farmer"
        assert db_user["state"] == "पंजाब (Punjab)"
        assert db_user["district"] == "बठिंडा (Bathinda)"
        print("[PASS] 2. User record securely verified in database")

        # 3. Verify Farm Record in DB
        db_farm = query_one("SELECT * FROM farms WHERE farmer_id = ?", (farmer_id,))
        assert db_farm is not None
        assert db_farm["total_area_acres"] == 4.5
        assert db_farm["soil_type"] == "दोमट मिट्टी (Loamy Soil)"
        print(f"[PASS] 3. Farm record created automatically: {db_farm['name']} ({db_farm['total_area_acres']} Acres)")

        # 4. Verify Crop Record in DB
        db_crop = query_one("SELECT * FROM crops WHERE farmer_id = ?", (farmer_id,))
        assert db_crop is not None
        assert db_crop["crop_name"] == "गेहूं (Wheat)"
        print(f"[PASS] 4. Crop record created automatically: {db_crop['crop_name']} (Health: {db_crop['health_status']})")

        # 5. Verify /api/auth/me works with registration session cookie
        session_id = res.cookies.get("agrigo_session")
        assert session_id, f"Session cookie not set. Response cookies: {res.cookies}"
        async with AsyncClient(transport=transport, base_url="http://testserver", cookies={"agrigo_session": session_id}) as me_client:
            me_res = await me_client.get("/api/auth/me")
            assert me_res.status_code == 200, f"/api/auth/me failed: {me_res.text}"
            me_data = me_res.json()
            assert me_data["authenticated"] is True
            assert me_data["user"]["id"] == farmer_id
            print(f"[PASS] 5. Session authentication verified via HttpOnly cookie: {me_data['user']['name']}")

        # 6. Verify duplicate phone registration is blocked with 400
        dup_res = await client.post("/api/auth/register", json=reg_payload)
        assert dup_res.status_code == 400, "Duplicate phone registration should return 400"
        print("[PASS] 6. Duplicate phone registration blocked (400 Bad Request)")

        # 7. Test Weather API with dynamic coordinates for chosen state & district
        weather_res = await client.get("/api/v1/agriculture/weather/detailed?lat=30.2110&lon=74.9455")
        assert weather_res.status_code == 200
        w_data = weather_res.json()
        assert "current" in w_data
        assert "forecast_7_days" in w_data
        print(f"[PASS] 7. Weather API responds for dynamic district (Bathinda, Punjab): {w_data['current']['temp']}°C ({w_data['current']['condition_hi']})")

    print("=" * 65)
    print(" ALL REGISTRATION & WEATHER VERIFICATION TESTS PASSED!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())
