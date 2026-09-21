import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from httpx import AsyncClient, ASGITransport
from app.main import app

async def run_integration_tests():
    print("=== STARTING AGRIGO SQLITE + VERIFIED INTERNET INTEGRATION TESTS ===")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health & Readiness
        res = await client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print(" [PASS] Health check OK:", res.json())

        res = await client.get("/ready")
        assert res.status_code == 200, f"Readiness check failed: {res.text}"
        print(" [PASS] Readiness check OK:", res.json())

        # 2. Fully Functional Real OTP Generation & Verification Flow
        otp_req_res = await client.post("/api/v1/auth/otp/request", json={"phone": "+919876543210"})
        assert otp_req_res.status_code == 200
        otp_data = otp_req_res.json()
        real_code = otp_data.get("otp_code")
        print(f" [PASS] Real OTP Generated: [{real_code}] for phone +919876543210")

        # Test verification with the exact real code
        verify_res = await client.post("/api/v1/auth/otp/verify", json={"phone": "+919876543210", "code": real_code})
        assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
        farmer_data = verify_res.json()
        print(f" [PASS] Real OTP Verified Successfully! Farmer: {farmer_data['user']['name']}, Token: {farmer_data['access_token'][:20]}...")

        # 3. Farmer Direct Login via ID & Password
        direct_login_res = await client.post("/api/v1/auth/farmer/login", json={"identifier": "9876543210", "password": "123456"})
        assert direct_login_res.status_code == 200
        print(" [PASS] Farmer Direct ID/Password Login OK:", direct_login_res.json()["user"]["name"])

        # 4. Verified Real-Time Agricultural Question (Specific Disease Query)
        chat_payload = {
            "question": "मेरे टमाटर के पत्ते ऊपर मुड़ रहे हैं (Tomato leaf curling), क्या करें?",
            "language": "hi",
            "crop_context": "Tomato"
        }
        chat_res = await client.post("/api/v1/chat/ask", json=chat_payload)
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        print("\n [PASS] Verified Agricultural AI Query Result:")
        print("   -> Provider:", chat_data["provider"])
        print("   -> Answer Excerpt:\n", chat_data["response"][:220], "...\n")
        print("   -> Verified Evidence Sources:", chat_data.get("evidence"))

        # 5. Admin Login & SQLite-Backed Control Center
        admin_res = await client.post("/api/v1/auth/admin/login", json={"email": "admin@agrigo.com", "password": "Admin@AgriGo2026"})
        assert admin_res.status_code == 200
        print(" [PASS] Admin Login OK:", admin_res.json()["user"]["full_name"])

        overview_res = await client.get("/api/v1/admin/overview")
        assert overview_res.status_code == 200
        print(" [PASS] SQLite Admin Overview Metrics:", overview_res.json())

        farmers_res = await client.get("/api/v1/admin/farmers")
        assert farmers_res.status_code == 200
        farmers_list = farmers_res.json()
        print(f" [PASS] Farmers in SQLite Database: {len(farmers_list)} farmers loaded")

        # 6. SQLite Farms, Crops & Reminders
        farms_res = await client.get("/api/v1/farms/")
        assert farms_res.status_code == 200
        print(f" [PASS] Farms in SQLite: {len(farms_res.json())} farm(s)")

        rem_res = await client.get("/api/v1/reminders/")
        assert rem_res.status_code == 200
        print(f" [PASS] Reminders in SQLite: {len(rem_res.json())} reminder(s)")

    print("\nALL SQLITE + VERIFIED INTERNET INTEGRATION TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
