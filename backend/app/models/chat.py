from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import datetime

class ChatMessage(BaseModel):
    id: Optional[str] = None
    sender: str  # "farmer" or "ai"
    content: str
    language: str = "en"
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    confidence_score: Optional[float] = None
    evidence_sources: List[str] = []
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class ConversationCreate(BaseModel):
    initial_message: Optional[str] = None
    language: str = "hi"

class ConversationResponse(BaseModel):
    id: str
    farmer_id: str
    language: str
    messages: List[ChatMessage] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

class ChatQueryRequest(BaseModel):
    farmer_id: Optional[str] = "farmer-1001"
    conversation_id: Optional[str] = None
    question: str
    language: Optional[str] = None
    crop_context: Optional[str] = None
    enable_voice: bool = False
