from app.adapters.vector.base import BaseVectorStore
from typing import List, Dict, Any

class MemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store with TF/IDF-style keyword token overlap scoring.
    Requires no external database, completely self-contained.
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []

    async def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        self.documents.append({
            "id": doc_id,
            "text": text,
            "tokens": set(text.lower().split()),
            "metadata": metadata
        })

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q_tokens = set(query.lower().split())
        scored = []
        for doc in self.documents:
            overlap = len(q_tokens.intersection(doc["tokens"]))
            if overlap > 0 or len(self.documents) < 5:
                score = overlap / (len(q_tokens) or 1)
                scored.append({
                    "id": doc["id"],
                    "content": doc["text"],
                    "score": score,
                    "title": doc["metadata"].get("title", "Agricultural Guide"),
                    "category": doc["metadata"].get("category", "General"),
                    "crop": doc["metadata"].get("crop", "General")
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
