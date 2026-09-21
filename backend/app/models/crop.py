from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class CropCycleCreate(BaseModel):
    farm_id: str
    crop_name: str
    variety: Optional[str] = None
    sowing_date: datetime.date
    expected_harvest_date: Optional[datetime.date] = None
    area_acres: float
    stage: str = "Sowing"  # Sowing, Vegetative, Flowering, Fruiting, Harvesting
    health_status: str = "Good"

class CropCycleResponse(CropCycleCreate):
    id: str
    farmer_id: str
    created_at: datetime.datetime

class IrrigationRecordCreate(BaseModel):
    crop_id: str
    field_name: str
    water_amount_liters: float
    method: str = "Drip"
    duration_minutes: int = 60

class HarvestRecordCreate(BaseModel):
    crop_id: str
    crop_name: str
    quantity_kg: float
    quality_grade: str = "A Grade"
    revenue_inr: Optional[float] = None
    harvest_date: datetime.date = Field(default_factory=datetime.date.today)
