from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.routes.auth import get_current_user
from app.models.outfit_history import OutfitHistory
from app.models.wardrobe import WardrobeItem

router = APIRouter()

class LogOutfitRequest(BaseModel):
    topId: Optional[str] = None
    bottomId: Optional[str] = None
    shoesId: Optional[str] = None
    onePieceId: Optional[str] = None
    occasion: str = ""

@router.post("/")
async def log_outfit(request: LogOutfitRequest, decoded_token: dict = Depends(get_current_user)):
    user_id = decoded_token["uid"]
    now = datetime.utcnow()
    
    # 1. Update lastWornDate on individual WardrobeItems
    item_ids = [req for req in [request.topId, request.bottomId, request.shoesId, request.onePieceId] if req]
    for iid in item_ids:
        try:
            item = await WardrobeItem.get(iid)
            if item and item.userId == user_id:
                item.lastWornDate = now
                await item.save()
        except Exception:
            pass
            
    # 2. Record the combination in OutfitHistory
    history_entry = OutfitHistory(
        userId=user_id,
        topId=request.topId,
        bottomId=request.bottomId,
        shoesId=request.shoesId,
        onePieceId=request.onePieceId,
        dateWorn=now,
        occasion=request.occasion
    )
    await history_entry.insert()
    
    return {"message": "Outfit logged successfully", "historyId": str(history_entry.id)}

@router.get("/")
async def get_outfit_history(decoded_token: dict = Depends(get_current_user)):
    user_id = decoded_token["uid"]
    # Return last 30 entries
    history = await OutfitHistory.find(OutfitHistory.userId == user_id).sort(-OutfitHistory.dateWorn).limit(30).to_list()
    return history
