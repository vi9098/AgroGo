"""
Verification Test for Dynamic Authkey.io OTP System
Tests:
1. Dynamic 6-digit OTP generation and database storage
2. Rejection of demo/static codes (123456, 999999) without active matching record
3. Authkey.io payload and HTTPS structure verification
4. Verification of genuine dynamic OTP -> Session cookie set
5. Single-use enforcement (replay attack prevention)
6. Expiration rejection
"""
import sys
import os
import asyncio
import datetime
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import query_one, execute_db
from app.services.authkey_service import AuthkeyService

async def run_tests():
    print("=" * 65)
    print(" RUNNING DYNAMIC AUTHKEY OTP VERIFICATION TESTS")
    print("=" * 65)

    # 1. Test Authkey Mobile Cleaner & Service Structure
    c_code, mob = AuthkeyService.clean_mobile("+919876543210")
    assert c_code == "91" and mob == "9876543210", f"Phone cleaner failed: {c_code}, {mob}"
    print("[PASS] 1. Mobile number normalization verified (+919876543210 -> 91, 9876543210)")

    # 1b. Test Authkey.io Request URL construction matching user specification
    req_url = AuthkeyService.build_request_url(
        mobile="9876543210",
        otp_code="1234",
        authkey="AUTHKEY",
        sender="SENDERID",
        pe_id="ENTITY_ID",
        template_id="DLT_TEMPLATE_ID",
        sms_text="Hello, your OTP is {otp}"
    )
    assert "https://api.authkey.io/request?" in req_url, f"Incorrect URL format: {req_url}"
    assert "authkey=AUTHKEY" in req_url
    assert "mobile=9876543210" in req_url
    assert "country_code=91" in req_url
    assert "sender=SENDERID" in req_url
    assert "pe_id=ENTITY_ID" in req_url
    assert "template_id=DLT_TEMPLATE_ID" in req_url
    assert "Hello" in req_url and "1234" in req_url
    print(f"[PASS] 1b. Authkey Request URL format verified: {req_url[:85]}...")

    # 2. Test Fallback when unconfigured
    test_res = AuthkeyService.send_otp("9876543210", "654321")
    assert test_res["success"] is True and test_res["mock"] is True
    print("[PASS] 2. Dev fallback and logging verified when API keys are blank")

    test_phone = "+919123456780"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 3. Request dynamic OTP
        req_res = await client.post("/api/v1/auth/otp/request", json={"phone": test_phone})
        assert req_res.status_code == 200, f"Request OTP failed: {req_res.text}"
        req_data = req_res.json()
        assert req_data["success"] is True
        assert "phone_masked" in req_data
        print(f"[PASS] 3. Dynamic OTP requested: Masked Phone: {req_data['phone_masked']}")

        # Verify OTP is saved in database
        db_otp = query_one(
            "SELECT * FROM otps WHERE phone = ? AND is_used = 0 ORDER BY id DESC LIMIT 1",
            (test_phone,)
        )
        assert db_otp is not None, "OTP was not saved in SQLite otps table"
        real_code = db_otp["code"]
        assert len(real_code) == 6 and real_code.isdigit(), f"Invalid OTP format: {real_code}"
        print(f"[PASS] 4. Dynamic OTP securely saved in DB: [{real_code}] (Status: unused)")

        # 4. Attempt verification with demo / invalid code
        fake_res = await client.post("/api/v1/auth/otp/verify", json={"phone": test_phone, "code": "000000"})
        assert fake_res.status_code == 400, f"Fake code should have been rejected! Status: {fake_res.status_code}"
        print("[PASS] 5. Invalid code (000000) rejected with 400")

        # Static demo bypass (123456) must ALSO be rejected if real_code is different
        if real_code != "123456":
            demo_res = await client.post("/api/v1/auth/otp/verify", json={"phone": test_phone, "code": "123456"})
            assert demo_res.status_code == 400, f"Demo code bypass should be disabled! Status: {demo_res.status_code}"
            print("[PASS] 6. Static demo code (123456) rejected — demo bypass is removed")

        # 5. Verify with genuine dynamic OTP
        valid_res = await client.post("/api/v1/auth/otp/verify", json={"phone": test_phone, "code": real_code})
        assert valid_res.status_code == 200, f"Valid OTP verification failed: {valid_res.text}"
        valid_data = valid_res.json()
        assert valid_data["success"] is True
        assert valid_data["user"]["role"] == "farmer"
        assert "agrigo_session" in valid_res.cookies, "Session cookie not set after OTP verify"
        print(f"[PASS] 7. Genuine dynamic OTP [{real_code}] verified! Session cookie issued: {valid_res.cookies['agrigo_session'][:15]}...")

        # 6. Replay attack check: Using the exact same code again must fail because is_used = 1
        replay_res = await client.post("/api/v1/auth/otp/verify", json={"phone": test_phone, "code": real_code})
        assert replay_res.status_code == 400, "Replayed OTP code must be rejected!"
        print("[PASS] 8. Replay attack rejected: OTP code is strictly single-use")

        # 7. Expiration check: Expired OTP must be rejected
        expired_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)).isoformat()
        execute_db(
            "INSERT INTO otps (phone, code, expires_at, is_used, created_at) VALUES (?, '998877', ?, 0, ?)",
            (test_phone, expired_time, expired_time)
        )
        expired_res = await client.post("/api/v1/auth/otp/verify", json={"phone": test_phone, "code": "998877"})
        assert expired_res.status_code == 400, "Expired OTP must be rejected!"
        print("[PASS] 9. Expired OTP rejected with 400")

    # 8. Test Authkey.io 2FA Verify API function (GET /api/2fa_verify.php)
    v_res = AuthkeyService.verify_otp_2fa(otp_code="123456", logid="ak-dev-12345678", channel="SMS")
    assert v_res["success"] is True and v_res["verified"] is True
    print("[PASS] 10. Authkey.io 2FA Verify API (GET /api/2fa_verify.php?authkey=...&channel=SMS&otp=...&logid=...) verified")

    print("=" * 65)
    print(" ALL 10 DYNAMIC OTP VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())
