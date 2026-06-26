from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/login")
@router.post("/sync")
async def login(decoded_token: dict = Depends(get_current_user)):
    user = await User.find_one(User.firebaseUid == decoded_token["uid"])
    if not user:
        user = User(
            firebaseUid=decoded_token["uid"],
            email=decoded_token.get("email", ""),
            name=decoded_token.get("name", "User"),
        )
        await user.insert()
    return user

@router.get("/verify")
async def verify(decoded_token: dict = Depends(get_current_user)):
    user = await User.find_one(User.firebaseUid == decoded_token["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
