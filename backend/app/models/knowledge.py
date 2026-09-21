from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class KnowledgeDocCreate(BaseModel):
    title: str
    category: str  # "crops", "diseases", "irrigation", "fertilizer", "pesticides"
    crop: Optional[str] = None
    content: str
    source: str
    verified: bool = True
    tags: List[str] = []

class KnowledgeDocResponse(KnowledgeDocCreate):
    id: str
    version: int = 1
    created_at: datetime.datetime
    updated_at: datetime.datetime

class KnowledgeSearchRequest(BaseModel):
    query: str
    crop: Optional[str] = None
    category: Optional[str] = None
    limit: int = 5
