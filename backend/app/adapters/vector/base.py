from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorStore(ABC):
    @abstractmethod
    async def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        pass
        
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass
