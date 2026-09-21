from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import datetime

class ConsentModel(BaseModel):
    farm_memory: bool = True
    ai_improvement: bool = False
    photo_learning: bool = False
    location_memory: bool = True
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class LocationModel(BaseModel):
    state: str = ""
    district: str = ""
    village: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FarmerCreate(BaseModel):
    phone: str
    name: str
    preferred_language: str = "hi"
    location: Optional[LocationModel] = None
    consent: Optional[ConsentModel] = None

class FarmerResponse(BaseModel):
    id: str
    phone: str
    name: str
    preferred_language: str
    location: LocationModel
    consent: ConsentModel
    created_at: datetime.datetime

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    code: str

class FarmerLoginRequest(BaseModel):
    identifier: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict
