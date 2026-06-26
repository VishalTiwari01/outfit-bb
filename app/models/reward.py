from beanie import Document
from datetime import datetime, timezone
from pydantic import Field

class AdReward(Document):
    userId: str
    credits: int
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "ad_rewards"
