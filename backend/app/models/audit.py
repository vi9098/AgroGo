from pydantic import BaseModel, Field
from typing import Optional, Dict
import datetime

class AuditLogEntry(BaseModel):
    id: Optional[str] = None
    actor_id: str
    actor_type: str  # "farmer", "admin", "system"
    action: str      # "LOGIN", "VIEW_FARMER_PROFILE", "EXPORT_DATA", etc.
    resource_type: str
    resource_id: Optional[str] = None
    ip_hash: Optional[str] = None
    details: Dict = Field(default_factory=dict)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
