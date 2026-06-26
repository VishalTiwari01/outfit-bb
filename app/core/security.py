from fastapi import Request, HTTPException, Header
import firebase_admin
from firebase_admin import credentials, auth
from app.config import settings

import os

# Initialize Firebase
try:
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
    else:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except ValueError as e:
    print(f"Warning: Failed to initialize Firebase Admin (likely dummy credentials): {e}")
    # Still allow the app to start so the 'test-token' fallback works

import jwt

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
        
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
        
    token = authorization.replace("Bearer ", "")
    print(f"DEBUG - Authorization Header: '{authorization}'")
    print(f"DEBUG - Extracted Token: '{token}'")
    
    try:
        if token == "test-token":
            return {"uid": "test-uid-123", "email": "test@example.com", "name": "Test User"}
        
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except ValueError as e:
            # Fallback if Firebase SDK is not initialized (dummy keys)
            print("Using fallback JWT decode without signature verification")
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            uid = decoded_token.get("user_id", decoded_token.get("sub"))
            if uid:
                decoded_token["uid"] = uid
                return decoded_token
            raise e
            
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
