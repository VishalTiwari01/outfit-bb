from beanie import Document
from typing import Optional

class User(Document):
    firebaseUid: str
    name: str
    email: str
    phone: Optional[str] = None
    avatarUrl: Optional[str] = None
    isPremium: bool = False
    credits: int = 0

    class Settings:
        name = "users"
