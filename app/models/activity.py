from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class ActivityLog(Document):
    userId: str
    action: str # UPLOAD, EDIT, DELETE, FAVORITE, UNFAVORITE
    wardrobeId: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "activity_logs"
