from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class ColorDetail(BaseModel):
    name: str
    hex: str
    percentage: Optional[int] = None

class ImageMetadata(BaseModel):
    imageUrl: str
    thumbnail: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None

class AIMetadata(BaseModel):
    category: Optional[str] = None
    fabric: Optional[str] = None
    pattern: Optional[str] = None
    style: Optional[str] = None

class WardrobeItem(Document):
    userId: str 
    title: str = ""
    image: Union[str, ImageMetadata, dict]
    
    # Classification
    category: Optional[str] = None
    subCategory: Optional[str] = None
    gender: Optional[str] = None
    colors: List[ColorDetail] = Field(default_factory=list)
    brand: Optional[str] = None
    
    # Details
    fabric: Optional[str] = None
    pattern: Optional[str] = None
    fit: Optional[str] = None
    sleeve: Optional[str] = None
    neck: Optional[str] = None
    season: Optional[str] = None
    
    # Status & Tracking
    status: str = "active" # active, archived, donated, sold, damaged
    laundryStatus: str = "clean" # clean, dirty, washing, ironing
    wearCount: int = 0
    lastWorn: Optional[datetime] = None
    firstWorn: Optional[datetime] = None
    
    # Relationships
    occasionIds: List[PydanticObjectId] = Field(default_factory=list)
    collectionIds: List[PydanticObjectId] = Field(default_factory=list)
    
    # Metadata
    purchaseDate: Optional[datetime] = None
    price: Optional[float] = None
    favorite: bool = False
    notes: str = ""
    
    # System
    aiMetadata: Optional[AIMetadata] = None
    deletedAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "wardrobe_items"

class WardrobeItemCreate(BaseModel):
    title: str = ""
    image: Union[str, ImageMetadata, dict]
    category: Optional[str] = None
    subCategory: Optional[str] = None
    gender: Optional[str] = None
    colors: List[ColorDetail] = Field(default_factory=list)
    brand: Optional[str] = None
    fabric: Optional[str] = None
    pattern: Optional[str] = None
    fit: Optional[str] = None
    sleeve: Optional[str] = None
    neck: Optional[str] = None
    season: Optional[str] = None
    status: str = "active"
    laundryStatus: str = "clean"
    occasionIds: List[str] = Field(default_factory=list)
    collectionIds: List[str] = Field(default_factory=list)
    purchaseDate: Optional[datetime] = None
    price: Optional[float] = None
    favorite: bool = False
    notes: str = ""
    aiMetadata: Optional[AIMetadata] = None
