from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.core.security import get_current_user
from app.models.user import User
from app.models.wardrobe import WardrobeItem, WardrobeItemCreate
from app.models.metadata import UserCollection, UserOccasion
from app.models.activity import ActivityLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

async def get_db_user(decoded_token: dict = Depends(get_current_user)):
    user = await User.find_one(User.firebaseUid == decoded_token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def log_activity(user_id: str, action: str, wardrobe_id: Optional[str] = None, details: Optional[str] = None):
    log = ActivityLog(userId=user_id, action=action, wardrobeId=wardrobe_id, details=details)
    await log.insert()

# ----------------- WARDROBE ITEMS -----------------

class SearchRequest(BaseModel):
    page: int = 1
    limit: int = 20
    sort: str = "createdAt"
    order: str = "desc" # "asc" or "desc"
    category: Optional[str] = None
    colors: Optional[List[str]] = None
    season: Optional[str] = None
    favorite: Optional[bool] = None
    brand: Optional[str] = None
    status: Optional[str] = "active"
    occasionId: Optional[str] = None
    collectionId: Optional[str] = None
    gender: Optional[str] = None

@router.post("/search")
async def search_items(search: SearchRequest, user: User = Depends(get_db_user)):
    query: Dict[str, Any] = {"userId": user.firebaseUid, "deletedAt": None}
    
    if search.category: query["category"] = search.category
    if search.season: query["season"] = search.season
    if search.favorite is not None: query["favorite"] = search.favorite
    if search.brand: query["brand"] = search.brand
    if search.status: query["status"] = search.status
    if search.gender: query["gender"] = search.gender
    if search.colors: query["colors.name"] = {"$in": search.colors}
    if search.occasionId: query["occasionIds"] = ObjectId(search.occasionId)
    if search.collectionId: query["collectionIds"] = ObjectId(search.collectionId)

    sort_order = -1 if search.order == "desc" else 1
    skip = (search.page - 1) * search.limit

    items = await WardrobeItem.find(query).sort([(search.sort, sort_order)]).skip(skip).limit(search.limit).to_list()
    total = await WardrobeItem.find(query).count()
    
    return {
        "data": items,
        "total": total,
        "page": search.page,
        "limit": search.limit
    }

@router.get("/")
async def get_items(page: int = 1, limit: int = 20, sort: str = "createdAt", order: str = "desc", user: User = Depends(get_db_user)):
    sort_order = -1 if order == "desc" else 1
    skip = (page - 1) * limit
    query = {"userId": user.firebaseUid, "deletedAt": None}
    items = await WardrobeItem.find(query).sort([(sort, sort_order)]).skip(skip).limit(limit).to_list()
    return items

@router.post("/", response_model=WardrobeItem)
async def add_item(item_create: WardrobeItemCreate, user: User = Depends(get_db_user)):
    item = WardrobeItem(**item_create.model_dump(), userId=user.firebaseUid)
    await item.insert()
    await log_activity(user.firebaseUid, "UPLOAD", str(item.id))
    return item

@router.put("/{item_id}", response_model=WardrobeItem)
async def update_item(item_id: str, item_update: Dict[str, Any], user: User = Depends(get_db_user)):
    try:
        from beanie import PydanticObjectId
        item = await WardrobeItem.get(PydanticObjectId(item_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Item ID")
    if not item or item.userId != user.firebaseUid or item.deletedAt is not None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_update["updatedAt"] = datetime.utcnow()
    await item.update({"$set": item_update})
    
    updated_item = await WardrobeItem.get(PydanticObjectId(item_id))
    
    # Track favorite changes specifically
    if "favorite" in item_update:
        action = "FAVORITE" if item_update["favorite"] else "UNFAVORITE"
        await log_activity(user.firebaseUid, action, str(updated_item.id))
    else:
        await log_activity(user.firebaseUid, "EDIT", str(updated_item.id))
        
    return updated_item

@router.delete("/{item_id}")
async def delete_item(item_id: str, user: User = Depends(get_db_user)):
    try:
        from beanie import PydanticObjectId
        item = await WardrobeItem.get(PydanticObjectId(item_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Item ID")
    if not item or item.userId != user.firebaseUid or item.deletedAt is not None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Soft delete
    item.deletedAt = datetime.utcnow()
    await item.save()
    
    await log_activity(user.firebaseUid, "DELETE", str(item.id))
    return {"message": "Item deleted"}

# ----------------- COLLECTIONS & OCCASIONS -----------------

@router.get("/collections")
async def get_collections(user: User = Depends(get_db_user)):
    return await UserCollection.find(UserCollection.userId == user.firebaseUid, UserCollection.deletedAt == None).to_list()

@router.post("/collections")
async def create_collection(name: str, description: str = None, user: User = Depends(get_db_user)):
    col = UserCollection(userId=user.firebaseUid, name=name, description=description)
    await col.insert()
    return col

@router.get("/occasions")
async def get_occasions(user: User = Depends(get_db_user)):
    return await UserOccasion.find(UserOccasion.userId == user.firebaseUid, UserOccasion.deletedAt == None).to_list()

@router.post("/occasions")
async def create_occasion(name: str, description: str = None, user: User = Depends(get_db_user)):
    occ = UserOccasion(userId=user.firebaseUid, name=name, description=description)
    await occ.insert()
    return occ
