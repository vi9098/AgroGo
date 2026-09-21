from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class FieldItem(BaseModel):
    id: Optional[str] = None
    name: str
    area_acres: float
    soil_type: str = "Loamy"
    current_crop: Optional[str] = None

class FarmCreate(BaseModel):
    name: str
    total_area_acres: float
    soil_type: str
    irrigation_type: str = "Drip"
    location: dict = Field(default_factory=dict)
    fields: List[FieldItem] = []

class FarmResponse(FarmCreate):
    id: str
    farmer_id: str
    created_at: datetime.datetime
