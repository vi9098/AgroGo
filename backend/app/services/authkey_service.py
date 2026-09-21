import http.client
import json
import logging
import os
import re
import secrets
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from app.config import settings

logger = logging.getLogger("agrigo.authkey")

class AuthkeyService:
    """
    Authkey.io Dynamic SMS OTP Integration Service.
    Dispatches dynamic OTPs via Authkey.io Request API:
    https://api.authkey.io/request?authkey=AUTHKEY&mobile=RecepientMobile&country_code=CountryCodeWithoutPlusSign&sms=Hello, your OTP is 1234&sender=SENDERID&pe_id=ENTITY_ID&template_id=DLT_TEMPLATE_ID
    and verifies submitted OTPs via Authkey.io 2FA Verify API:
    https://console.authkey.io/api/2fa_verify.php?authkey=AUTHKEY&channel=SMS/VOICE/EMAIL&otp=OTP VALUE ENTERED BY CUSTOMER&logid=LogID GENERATED ON REQUEST API
    """

    @staticmethod
    def clean_mobile(phone: str) -> Tuple[str, str]:
        """
        Normalizes Indian and international phone numbers.
        Returns (country_code, mobile_without_country_code).
        Example: '+919876543210' -> ('91', '9876543210')
        """
        cleaned = re.sub(r"[^\d]", "", phone.strip())
        if cleaned.startswith("91") and len(cleaned) == 12:
            return "91", cleaned[2:]
        if len(cleaned) == 10:
            return "91", cleaned
        if len(cleaned) > 10:
            return cleaned[:-10], cleaned[-10:]
        return "91", cleaned

    @classmethod
    def build_request_url(
        cls,
        mobile: str,
        otp_code: str,
        authkey: Optional[str] = None,
        sender: Optional[str] = None,
        pe_id: Optional[str] = None,
        template_id: Optional[str] = None,
        sms_text: Optional[str] = None,
        country_code: Optional[str] = None,
        host: Optional[str] = None
    ) -> str:
        """
        Constructs the exact Authkey.io Request URL:
        https://api.authkey.io/request?authkey=AUTHKEY&mobile=RecepientMobile&country_code=CountryCodeWithoutPlusSign&sms=Hello, your OTP is 1234&sender=SENDERID&pe_id=ENTITY_ID&template_id=DLT_TEMPLATE_ID
        """
        resolved_api_key = authkey or os.getenv("AUTHKEY_API_KEY") or getattr(settings, "AUTHKEY_API_KEY", None) or "AUTHKEY"
        resolved_sender = sender or os.getenv("AUTHKEY_SENDER") or getattr(settings, "AUTHKEY_SENDER", "AGRIGO") or "SENDERID"
        resolved_pe_id = pe_id or os.getenv("AUTHKEY_PE_ID") or getattr(settings, "AUTHKEY_PE_ID", None)
        resolved_template_id = template_id or os.getenv("AUTHKEY_TEMPLATE_ID") or getattr(settings, "AUTHKEY_TEMPLATE_ID", None)
        sms_template = sms_text or os.getenv("AUTHKEY_SMS_TEMPLATE") or getattr(settings, "AUTHKEY_SMS_TEMPLATE", None) or "Hello, your OTP is {otp}"
        formatted_sms = sms_template.replace("{otp}", str(otp_code)).replace("{OTP}", str(otp_code))

        c_code, clean_phone = cls.clean_mobile(mobile)
        if country_code:
            c_code = country_code.replace("+", "").strip()

        raw_host = host or os.getenv("AUTHKEY_HOST") or getattr(settings, "AUTHKEY_HOST", "api.authkey.io")
        authkey_host = raw_host.replace("https://", "").replace("http://", "").strip("/")

        params = {
            "authkey": resolved_api_key,
            "mobile": clean_phone,
            "country_code": c_code,
            "sms": formatted_sms,
            "sender": resolved_sender,
        }
        if resolved_pe_id:
            params["pe_id"] = str(resolved_pe_id).strip()
        if resolved_template_id:
            params["template_id"] = str(resolved_template_id).strip()

        query_string = urllib.parse.urlencode(params)
        return f"https://{authkey_host}/request?{query_string}"

    @classmethod
    def send_otp(
        cls,
        mobile: str,
        otp_code: str,
        api_key: Optional[str] = None,
        sender: Optional[str] = None,
        pe_id: Optional[str] = None,
        template_id: Optional[str] = None,
        sms_text: Optional[str] = None,
        sid: Optional[str] = None,
        host: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends dynamic OTP via Authkey.io Request API:
        https://api.authkey.io/request?authkey=AUTHKEY&mobile=RecepientMobile&country_code=CountryCodeWithoutPlusSign&sms=Hello, your OTP is 1234&sender=SENDERID&pe_id=ENTITY_ID&template_id=DLT_TEMPLATE_ID
        """
        country_code, clean_phone = cls.clean_mobile(mobile)

        resolved_api_key = api_key or os.getenv("AUTHKEY_API_KEY") or getattr(settings, "AUTHKEY_API_KEY", None)
        resolved_sender = sender or os.getenv("AUTHKEY_SENDER") or getattr(settings, "AUTHKEY_SENDER", "AGRIGO")
        resolved_pe_id = pe_id or os.getenv("AUTHKEY_PE_ID") or getattr(settings, "AUTHKEY_PE_ID", None)
        resolved_template_id = template_id or os.getenv("AUTHKEY_TEMPLATE_ID") or getattr(settings, "AUTHKEY_TEMPLATE_ID", None)
        sms_template = sms_text or os.getenv("AUTHKEY_SMS_TEMPLATE") or getattr(settings, "AUTHKEY_SMS_TEMPLATE", None) or "Hello, your OTP is {otp}"
        formatted_sms = sms_template.replace("{otp}", str(otp_code)).replace("{OTP}", str(otp_code))
        resolved_sid = sid or os.getenv("AUTHKEY_SID") or getattr(settings, "AUTHKEY_SID", None)
        raw_host = host or os.getenv("AUTHKEY_HOST") or getattr(settings, "AUTHKEY_HOST", "api.authkey.io")
        authkey_host = raw_host.replace("https://", "").replace("http://", "").strip("/")

        # Check if real Authkey credentials are configured
        is_configured = (
            resolved_api_key
            and not str(resolved_api_key).startswith("<")
            and len(str(resolved_api_key).strip()) > 5
        )

        if not is_configured:
            dev_logid = f"ak-dev-{secrets.token_hex(8)}"
            logger.info(
                f"[Authkey.io Dev Fallback] AUTHKEY_API_KEY not configured in environment. "
                f"Generated dynamic OTP for +{country_code} {clean_phone} -> [{otp_code}] (LogID: {dev_logid})."
            )
            return {
                "success": True,
                "dispatched": False,
                "mock": True,
                "message": "Authkey credentials not configured. Dynamic OTP generated and stored in database.",
                "mobile": clean_phone,
                "country_code": country_code,
                "code": otp_code,
                "logid": dev_logid
            }

        # Check if legacy SID template API is specifically requested
        if resolved_sid and resolved_sid != "**" and not resolved_template_id and "console.authkey.io" in authkey_host:
            auth_header = resolved_api_key.strip()
            if not auth_header.lower().startswith("basic "):
                auth_header = f"Basic {auth_header}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': auth_header
            }
            payload = json.dumps({
                "country_code": country_code,
                "mobile": clean_phone,
                "sid": str(resolved_sid).strip(),
                "otp": str(otp_code),
                "bodyValues": {"otp": str(otp_code), "2fa": str(otp_code)}
            })
            method = "POST"
            path = "/restapi/requestjson.php"
        else:
            # Primary standard: https://api.authkey.io/request?authkey=...
            params = {
                "authkey": resolved_api_key.strip(),
                "mobile": clean_phone,
                "country_code": country_code,
                "sms": formatted_sms,
                "sender": str(resolved_sender).strip() if resolved_sender else "AGRIGO",
            }
            if resolved_pe_id:
                params["pe_id"] = str(resolved_pe_id).strip()
            if resolved_template_id:
                params["template_id"] = str(resolved_template_id).strip()

            query_string = urllib.parse.urlencode(params)
            method = "GET"
            path = f"/request?{query_string}"
            headers = {}
            payload = None

        try:
            masked_key = f"{resolved_api_key[:4]}...{resolved_api_key[-4:]}" if len(resolved_api_key) > 8 else "***"
            logger.info(f"[Authkey.io] Requesting dynamic OTP SMS: https://{authkey_host}{path.split('?')[0]} for +{country_code} {clean_phone} (authkey={masked_key})...")
            conn = http.client.HTTPSConnection(authkey_host, timeout=12)
            conn.request(method, path, body=payload, headers=headers)
            res = conn.getresponse()
            raw_response = res.read().decode("utf-8")
            status_code = res.status
            conn.close()

            logger.info(f"[Authkey.io] HTTP {status_code} Response: {raw_response}")

            try:
                data = json.loads(raw_response)
            except Exception:
                data = {"raw": raw_response}

            # Extract logid from Authkey response
            logid = None
            if isinstance(data, dict):
                logid = (
                    data.get("logid")
                    or data.get("log_id")
                    or data.get("LogID")
                    or data.get("logId")
                )
                if not logid and isinstance(data.get("data"), dict):
                    logid = (
                        data["data"].get("logid")
                        or data["data"].get("log_id")
                        or data["data"].get("LogID")
                        or data["data"].get("logId")
                    )

            if not logid and isinstance(raw_response, str):
                m = re.search(r'["\']?logid["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)', raw_response, re.IGNORECASE)
                if m:
                    logid = m.group(1)

            if not logid:
                logid = f"ak-res-{secrets.token_hex(8)}"

            # Authkey response status verification
            is_success = status_code in (200, 201)
            if isinstance(data, dict):
                if data.get("status") in ("error", "failed", 400, 401, 403, 500):
                    is_success = False
                if str(data.get("code")) in ("400", "401", "403", "500"):
                    is_success = False

            return {
                "success": is_success,
                "dispatched": True,
                "mock": False,
                "status_code": status_code,
                "response": data,
                "mobile": clean_phone,
                "country_code": country_code,
                "logid": str(logid)
            }
        except Exception as e:
            logger.error(f"[Authkey.io Connection Error] Failed to contact Authkey API: {e}", exc_info=True)
            return {
                "success": False,
                "dispatched": False,
                "mock": False,
                "error": str(e),
                "mobile": clean_phone,
                "country_code": country_code,
                "logid": None
            }

    @classmethod
    def verify_otp_2fa(
        cls,
        otp_code: str,
        logid: Optional[str] = None,
        channel: str = "SMS",
        api_key: Optional[str] = None,
        host: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies dynamic OTP via Authkey.io 2FA Verify API:
        GET https://console.authkey.io/api/2fa_verify.php?authkey=AUTHKEY&channel=SMS/VOICE/EMAIL&otp=OTP&logid=LogID
        """
        resolved_api_key = api_key or os.getenv("AUTHKEY_API_KEY") or getattr(settings, "AUTHKEY_API_KEY", None)
        raw_host = host or os.getenv("AUTHKEY_HOST") or getattr(settings, "AUTHKEY_HOST", "console.authkey.io")
        authkey_host = raw_host.replace("https://", "").replace("http://", "").strip("/")

        is_configured = (
            resolved_api_key
            and not resolved_api_key.startswith("<")
            and len(resolved_api_key.strip()) > 5
        )

        clean_code = str(otp_code).strip()
        clean_logid = str(logid or "").strip()

        # If running in mock/dev mode or credentials unconfigured or dev logid:
        if not is_configured or not clean_logid or clean_logid.startswith("ak-dev-"):
            logger.info(f"[Authkey.io 2FA Verify Dev Fallback] OTP: {clean_code}, LogID: {clean_logid}")
            return {
                "success": True,
                "verified": True,
                "mock": True,
                "message": "Dev mode OTP verified successfully."
            }

        params = urllib.parse.urlencode({
            "authkey": resolved_api_key.strip(),
            "channel": channel or "SMS",
            "otp": clean_code,
            "logid": clean_logid
        })
        url_path = f"/api/2fa_verify.php?{params}"

        try:
            logger.info(f"[Authkey.io 2FA Verify] Connecting to {authkey_host}/api/2fa_verify.php?channel={channel}&otp={clean_code}&logid={clean_logid}...")
            conn = http.client.HTTPSConnection(authkey_host, timeout=12)
            conn.request("GET", url_path)
            res = conn.getresponse()
            raw_response = res.read().decode("utf-8")
            status_code = res.status
            conn.close()

            logger.info(f"[Authkey.io 2FA Verify] HTTP {status_code} Response: {raw_response}")
            try:
                data = json.loads(raw_response)
            except Exception:
                data = {"raw": raw_response}

            # Authkey response parsing:
            # Usually {"status": 200, "message": "OTP Verified Successfully"} or {"status": 400, "message": "Invalid OTP"}
            is_verified = False
            message = "OTP verification failed."
            if isinstance(data, dict):
                st = data.get("status")
                msg = str(data.get("message", "")).lower()
                if st in (200, 201, "200", "success", True) or "verified" in msg or "success" in msg:
                    is_verified = True
                    message = data.get("message", "OTP Verified Successfully.")
                else:
                    is_verified = False
                    message = data.get("message", "Invalid or expired OTP.")
            elif status_code in (200, 201):
                is_verified = True
                message = "OTP Verified Successfully."

            return {
                "success": is_verified,
                "verified": is_verified,
                "mock": False,
                "status_code": status_code,
                "message": message,
                "response": data
            }
        except Exception as e:
            logger.error(f"[Authkey.io 2FA Verify Error] Failed to contact Authkey API: {e}", exc_info=True)
            return {
                "success": False,
                "verified": False,
                "mock": False,
                "error": str(e),
                "message": f"Authkey verification request failed: {e}"
            }
