from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSTTAdapter(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> Dict[str, Any]:
        pass
