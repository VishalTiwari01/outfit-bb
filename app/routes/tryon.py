from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List, Optional
import shutil
import tempfile
import os
import asyncio
import cloudinary
import cloudinary.uploader
from app.config import settings
from app.core.security import get_current_user
from app.models.tryon import TryOnHistory
from dotenv import load_dotenv
from gradio_client import Client, handle_file
from fastapi.concurrency import run_in_threadpool
from PIL import Image

router = APIRouter()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

@router.post("/generate")
async def generate_tryon(
    user_image: UploadFile = File(...),
    top_image: UploadFile = File(...),
    bottom_image: Optional[UploadFile] = File(None),
    occasion: str = Form(...),
    category: str = Form("Unknown"),
    gender: str = Form("Unknown"),
    color: str = Form("Unknown"),
    fabric: str = Form("Unknown"),
    pattern: str = Form("Unknown"),
    fit: str = Form("Unknown"),
    sleeve: str = Form("Unknown"),
    style: str = Form("Unknown"),
    decoded_token: dict = Depends(get_current_user)
):
    user_id = decoded_token["uid"]
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Temporary Storage (Convert to RGB to prevent RGBA as JPEG errors in Gradio)
        user_img_path = os.path.join(temp_dir, "user_image.jpg")
        top_img_path = os.path.join(temp_dir, "top_image.jpg")
        
        user_pil = Image.open(user_image.file)
        if user_pil.mode in ("RGBA", "P"):
            user_pil = user_pil.convert("RGB")
        user_pil.save(user_img_path, "JPEG")
            
        top_pil = Image.open(top_image.file)
        if top_pil.mode in ("RGBA", "P"):
            top_pil = top_pil.convert("RGB")
        top_pil.save(top_img_path, "JPEG")
        
        bottom_img_path = None
        if bottom_image:
            bottom_img_path = os.path.join(temp_dir, "bottom_image.jpg")
            bottom_pil = Image.open(bottom_image.file)
            if bottom_pil.mode in ("RGBA", "P"):
                bottom_pil = bottom_pil.convert("RGB")
            bottom_pil.save(bottom_img_path, "JPEG")
            
        # 2. Virtual Try-On ML Call via HuggingFace Space
        
        # Force reload .env so we don't have to restart the backend server manually
        load_dotenv(override=True)
        hf_token = os.getenv("HF_TOKEN") or settings.HF_TOKEN
        
        client = Client("Kwai-Kolors/Kolors-Virtual-Try-On", token=hf_token) if hf_token else Client("Kwai-Kolors/Kolors-Virtual-Try-On")
        
        # Bypass Gradio's restriction on api_name=False
        client.endpoints[2].api_name = '/predict'
        client.endpoints[2].is_valid = True
        
        import asyncio
        max_retries = 5
        
        async def call_predict_with_retry(img1, img2):
            for attempt in range(max_retries):
                try:
                    return await run_in_threadpool(
                        client.predict,
                        handle_file(img1),
                        handle_file(img2),
                        42, # seed
                        True, # randomize_seed
                        fn_index=2
                    )
                except Exception as e:
                    err_msg = str(e)
                    should_retry = (
                        "Too many users" in err_msg or 
                        "queue" in err_msg.lower() or 
                        "upstream gradio app has raised an exception" in err_msg.lower() or
                        "404 not found" in err_msg.lower() or
                        "50" in err_msg # 500, 502, 503, 504 server errors
                    )
                    
                    if should_retry and attempt < max_retries - 1:
                        print(f"HF Server overloaded/crashed. Retrying {attempt + 1}/{max_retries} in 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    raise e

        try:
            # Pass 1: Top Garment Try-On
            result_top = await call_predict_with_retry(user_img_path, top_img_path)
            
            if isinstance(result_top, (list, tuple)):
                generated_img_path = result_top[0]
            else:
                generated_img_path = result_top
                
            # Pass 2: Bottom Garment Try-On (if provided)
            if bottom_img_path:
                result_bottom = await call_predict_with_retry(generated_img_path, bottom_img_path)
                
                if isinstance(result_bottom, (list, tuple)):
                    generated_img_path = result_bottom[0]
                else:
                    generated_img_path = result_bottom
        except Exception as e:
            err_msg = str(e)
            if "Too many users" in err_msg or "queue" in err_msg.lower():
                raise HTTPException(status_code=503, detail="The AI server is currently heavily overloaded. Please try again later, or duplicate the HF Space for private access.")
            raise HTTPException(status_code=500, detail=f"AI Model Error: {err_msg}")
        # 3. Cloudinary Uploads with Fallback
        try:
            # Upload user image
            user_upload = cloudinary.uploader.upload(user_img_path)
            user_img_url = user_upload.get("secure_url")
            
            # Upload dress image
            dress_upload = cloudinary.uploader.upload(top_img_path)
            dress_img_url = dress_upload.get("secure_url")
            
            # Upload generated image
            result_upload = cloudinary.uploader.upload(generated_img_path)
            result_img_url = result_upload.get("secure_url")
        except Exception as upload_err:
            print(f"Cloudinary upload failed: {upload_err}. Falling back to base64.")
            import base64
            with open(user_img_path, "rb") as f:
                user_img_url = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            with open(top_img_path, "rb") as f:
                dress_img_url = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            with open(generated_img_path, "rb") as f:
                result_img_url = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        
        # 4. MongoDB Storage
        history_entry = TryOnHistory(
            userId=user_id,
            userImage=user_img_url,
            dressImage=dress_img_url,
            resultImage=result_img_url,
            occasion=occasion,
            status="completed"
        )
        await history_entry.insert()
        
        return {
            "message": "Try-On generated successfully",
            "resultImage": result_img_url,
            "historyId": str(history_entry.id)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "ZeroGPU quota" in error_msg:
            raise HTTPException(
                status_code=429, 
                detail="Our free AI Server is currently at full capacity (ZeroGPU quota exceeded). Please wait about 5 minutes and try again."
            )
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        # Cleanup temporary files
        shutil.rmtree(temp_dir)

@router.get("/history")
async def get_tryon_history(decoded_token: dict = Depends(get_current_user)):
    user_id = decoded_token["uid"]
    history = await TryOnHistory.find(TryOnHistory.userId == user_id).sort(-TryOnHistory.createdAt).to_list()
    return history
