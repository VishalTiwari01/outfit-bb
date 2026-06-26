from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, model_validator
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

class Colors(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[str] = None

class WardrobeItem(Document):
    userId: str 
    title: str = ""
    imageUrl: str = ""
    image: Optional[Any] = None
    thumbnail: Optional[str] = None
    
    # Classification
    category: Optional[str] = None
    subcategory: Optional[str] = None
    gender: Optional[str] = None
    colors: Optional[Union[Colors, Dict[str, Any], Any]] = Field(default_factory=Colors)
    color: Optional[Any] = None
    brand: Optional[str] = None
    
    # AI Extracted Attributes
    pattern: Optional[str] = None
    material: Optional[str] = None
    fabric: Optional[str] = None
    texture: Optional[str] = None
    transparency: Optional[str] = None
    fit: Optional[str] = None
    length: Optional[str] = None
    neck: Optional[str] = None
    collarType: Optional[str] = None
    sleeve: Optional[str] = None
    pocketCount: Optional[int] = 0
    buttonType: Optional[str] = None
    closureType: Optional[str] = None
    printType: Optional[str] = None
    layerType: Optional[str] = None
    
    # Context & Style
    style: Optional[str] = None
    fashionStyle: Optional[str] = None
    dressCode: Optional[str] = None
    season: Optional[List[str]] = Field(default_factory=list)
    seasonTags: Optional[List[str]] = None
    occasion: Optional[List[str]] = Field(default_factory=list)
    occasionTags: Optional[List[str]] = None
    ageGroup: Optional[str] = None
    
    # AI Scoring
    weatherScore: Optional[float] = None
    luxuryScore: Optional[float] = None
    casualScore: Optional[float] = None
    formalityScore: Optional[float] = None
    
    # Vector Search
    embedding: List[float] = Field(default_factory=list)
    confidence: Optional[float] = None
    
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
    deletedAt: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "wardrobe_items"

    @model_validator(mode='before')
    @classmethod
    def handle_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Fix imageUrl
            if not data.get('imageUrl'):
                if 'image' in data:
                    img = data['image']
                    if isinstance(img, str):
                        data['imageUrl'] = img
                    elif isinstance(img, dict) and 'url' in img:
                        data['imageUrl'] = img['url']
                    else:
                        data['imageUrl'] = ""
                else:
                    data['imageUrl'] = ""
                    
            # Fix colors (if it's a list or None)
            if 'colors' in data and not isinstance(data['colors'], dict):
                data['colors'] = {'primary': None, 'secondary': None}
                
            if 'color' in data and data.get('color'):
                if isinstance(data['color'], dict) and 'name' in data['color']:
                    data['colors'] = {'primary': data['color']['name'], 'secondary': None}

            # Fix season (if it's None)
            if data.get('season') is None:
                data['season'] = data.get('seasonTags') or []
                
            # Fix occasion (if it's None)
            if data.get('occasion') is None:
                data['occasion'] = data.get('occasionTags') or []
                
        return data

class WardrobeItemCreate(BaseModel):
    title: str = ""
    imageUrl: str
    thumbnail: Optional[str] = None
    
    category: Optional[str] = None
    subcategory: Optional[str] = None
    gender: Optional[str] = None
    colors: Colors = Field(default_factory=Colors)
    brand: Optional[str] = None
    logoPresent: bool = False
    
    pattern: Optional[str] = None
    material: Optional[str] = None
    fabric: Optional[str] = None
    texture: Optional[str] = None
    transparency: Optional[str] = None
    fit: Optional[str] = None
    length: Optional[str] = None
    neck: Optional[str] = None
    collarType: Optional[str] = None
    sleeve: Optional[str] = None
    pocketCount: Optional[int] = 0
    buttonType: Optional[str] = None
    closureType: Optional[str] = None
    printType: Optional[str] = None
    layerType: Optional[str] = None
    
    style: Optional[str] = None
    fashionStyle: Optional[str] = None
    dressCode: Optional[str] = None
    season: List[str] = Field(default_factory=list)
    occasion: List[str] = Field(default_factory=list)
    ageGroup: Optional[str] = None
    
    weatherScore: Optional[float] = None
    luxuryScore: Optional[float] = None
    casualScore: Optional[float] = None
    formalityScore: Optional[float] = None
    
    embedding: List[float] = Field(default_factory=list)
    confidence: Optional[float] = None
