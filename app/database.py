from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.models.reward import AdReward
from app.models.outfit_history import OutfitHistory
from app.models.tryon import TryOnHistory, Occasion
from app.models.metadata import Category, SubCategory, Brand, SystemColor, UserCollection, UserOccasion
from app.models.activity import ActivityLog
import urllib.parse
import certifi

async def init_db():
    # Fix parsing of MongoDB URI with query params
    client = AsyncIOMotorClient(settings.MONGODB_URI, tlsCAFile=certifi.where())
    parsed_uri = urllib.parse.urlparse(settings.MONGODB_URI)
    db_name = parsed_uri.path.lstrip("/")
    if not db_name:
        db_name = "outfit"
    await init_beanie(database=client[db_name], document_models=[
        User, WardrobeItem, AdReward, OutfitHistory, TryOnHistory, Occasion,
        Category, SubCategory, Brand, SystemColor, UserCollection, UserOccasion, ActivityLog
    ])
