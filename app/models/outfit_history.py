from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class OutfitHistory(Document):
    userId: str
    topId: Optional[str] = None
    bottomId: Optional[str] = None
    shoesId: Optional[str] = None
    onePieceId: Optional[str] = None
    dateWorn: datetime = Field(default_factory=datetime.utcnow)
    occasion: str = ""

    class Settings:
        name = "outfit_history"
