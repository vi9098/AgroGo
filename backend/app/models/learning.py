from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class ObservationCreate(BaseModel):
    crop_name: str
    symptoms: str
    suspected_issue: Optional[str] = None
    photo_ids: List[str] = []
    region: str = ""

class LearningCandidateResponse(BaseModel):
    id: str
    source_observation_id: str
    crop: str
    proposed_fact: str
    confidence_score: float
    status: str = "pending"  # pending, approved, rejected
    reviewer_notes: Optional[str] = None
    created_at: datetime.datetime
