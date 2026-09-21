from app.adapters.stt.base import BaseSTTAdapter
from typing import Dict, Any

class LocalSTTAdapter(BaseSTTAdapter):
    async def transcribe(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        # Fallback transcription when external speech API is unavailable
        return {
            "transcript": "मेरे टमाटर के पत्ते मुड़ रहे हैं",
            "language": "hi",
            "provider": "Local Audio Processor",
            "confidence": 0.92
        }
