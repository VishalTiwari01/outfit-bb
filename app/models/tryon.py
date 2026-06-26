from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class Occasion(Document):
    name: str
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "occasions"

class TryOnHistory(Document):
    userId: str
    userImage: str
    dressImage: str
    resultImage: str
    occasion: str
    status: str = "completed"
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "tryon_history"
