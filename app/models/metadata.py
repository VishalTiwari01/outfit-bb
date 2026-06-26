from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional

class Category(Document):
    name: str
    description: Optional[str] = None
    isActive: bool = True

    class Settings:
        name = "categories"

class SubCategory(Document):
    name: str
    categoryId: str
    isActive: bool = True

    class Settings:
        name = "sub_categories"

class Brand(Document):
    name: str
    isActive: bool = True

    class Settings:
        name = "brands"

class SystemColor(Document):
    name: str
    hex: str
    isActive: bool = True

    class Settings:
        name = "system_colors"

class UserCollection(Document):
    userId: str
    name: str
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    deletedAt: Optional[datetime] = None

    class Settings:
        name = "user_collections"

class UserOccasion(Document):
    userId: str
    name: str
    description: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    deletedAt: Optional[datetime] = None

    class Settings:
        name = "user_occasions"
