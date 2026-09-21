from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "analyst"  # admin, analyst, reviewer
    enable_2fa: bool = False

class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_2fa_enabled: bool
    created_at: datetime.datetime
