from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AgriGo Secure Agriculture AI"
    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017/agrigo"
    MONGODB_DB_NAME: str = "agrigo"
    
    # Security & Tokens
    JWT_SECRET: str = "agrigo-super-secure-jwt-secret-key-2026-production-minimum-32bytes"
    JWT_REFRESH_SECRET: str = "agrigo-refresh-secret-key-2026-production-minimum-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://agrigo.vercel.app",
        "*"
    ]
    
    # Storage
    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIR: str = "./uploads"
    
    # Providers
    PRIMARY_LLM_PROVIDER: str = "gemini"
    SECONDARY_LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # Kindwise Crop Health & Insect ID APIs
    KINDWISE_CROP_KEY: Optional[str] = None
    KINDWISE_INSECT_KEY: Optional[str] = None
    
    PRIMARY_STT_PROVIDER: str = "google"
    GOOGLE_STT_KEY: Optional[str] = None
    
    PRIMARY_TTS_PROVIDER: str = "google"
    GOOGLE_TTS_KEY: Optional[str] = None
    
    # Vector DB
    VECTOR_PROVIDER: str = "memory"  # memory | mongodb | qdrant
    
    # Admin 2FA
    ADMIN_2FA_ISSUER: str = "AgriGo Command Center"

    # Authkey.io Dynamic SMS OTP Integration (api.authkey.io & console.authkey.io)
    # Request: https://api.authkey.io/request?authkey=AUTHKEY&mobile=RecepientMobile&country_code=CountryCodeWithoutPlusSign&sms=Hello, your OTP is 1234&sender=SENDERID&pe_id=ENTITY_ID&template_id=DLT_TEMPLATE_ID
    # Verify:  https://console.authkey.io/api/2fa_verify.php?authkey=AUTHKEY&channel=SMS&otp=OTP&logid=LogID
    AUTHKEY_API_KEY: Optional[str] = None
    AUTHKEY_SENDER: Optional[str] = "AGRIGO"
    AUTHKEY_PE_ID: Optional[str] = None
    AUTHKEY_TEMPLATE_ID: Optional[str] = None
    AUTHKEY_SMS_TEMPLATE: Optional[str] = "Hello, your OTP is {otp}"
    AUTHKEY_SID: Optional[str] = None
    AUTHKEY_HOST: str = "api.authkey.io"
    # Supabase Cloud Database & Storage
    SUPABASE_URL: Optional[str] = "https://lebkgjebavldqqflwwox.supabase.co"
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
