from pydantic import BaseModel
from typing import Dict, Any

class ProviderStatus(BaseModel):
    name: str
    service_type: str  # STT, LLM, TTS, DB, Vector, Storage
    is_operational: bool
    latency_ms: float
    provider_name: str
    details: str = ""
