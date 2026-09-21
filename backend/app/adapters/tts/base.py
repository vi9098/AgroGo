from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTTSAdapter(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language: str) -> Dict[str, Any]:
        pass
