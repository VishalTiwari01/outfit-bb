from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.reward import AdReward
from app.models.user import User

router = APIRouter()

async def get_db_user(decoded_token: dict = Depends(get_current_user)):
    user = await User.find_one(User.firebaseUid == decoded_token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/ad")
async def claim_ad_reward(user: User = Depends(get_db_user)):
    # Create an AdReward log
    reward = AdReward(userId=user.firebaseUid, credits=1)
    await reward.insert()
    
    # Increment user credits
    user.credits += 1
    await user.save()
    
    return {"message": "Credit added successfully", "total_credits": user.credits}
