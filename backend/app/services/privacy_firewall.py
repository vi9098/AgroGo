import re
from typing import Dict, Any

class PrivacyFirewall:
    """
    Detects and redacts sensitive PII before forwarding data to external AI providers.
    Enforces the minimization principle.
    """
    
    PHONE_REGEX = re.compile(r'(\+?[0-9]{1,3}[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?)?[0-9]{3}[-.\s]?[0-9]{4}')
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    AADHAAR_REGEX = re.compile(r'\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b')

    @classmethod
    def sanitize_prompt(cls, text: str) -> str:
        if not text:
            return ""
        redacted = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", text)
        redacted = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", redacted)
        redacted = cls.AADHAAR_REGEX.sub("[ID_REDACTED]", redacted)
        return redacted

    @classmethod
    def minimize_farmer_context(cls, farmer_data: Dict[str, Any], allowed_consent: bool) -> Dict[str, Any]:
        """
        Minimizes context. Only agricultural specifics are forwarded, NOT private farmer info.
        """
        context = {
            "crop": farmer_data.get("current_crop", "General Crop"),
            "region": farmer_data.get("state", "India"),
            "soil_type": farmer_data.get("soil_type", "Standard"),
            "irrigation": farmer_data.get("irrigation_type", "General")
        }
        return context
