from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
        pass
