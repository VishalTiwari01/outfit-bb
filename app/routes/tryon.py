from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List
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
    dress_images: List[UploadFile] = File(...),
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
        dress_img_path = os.path.join(temp_dir, "dress_image.jpg")
        
        user_pil = Image.open(user_image.file)
        if user_pil.mode in ("RGBA", "P"):
            user_pil = user_pil.convert("RGB")
        user_pil.save(user_img_path, "JPEG")
            
        # Process and stitch multiple dress images if provided
        dress_pils = []
        for d_img in dress_images:
            pil_img = Image.open(d_img.file)
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            dress_pils.append(pil_img)
            
        if len(dress_pils) > 1:
            # Stitch them vertically
            total_height = sum(img.height for img in dress_pils)
            max_width = max(img.width for img in dress_pils)
            merged_img = Image.new("RGB", (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in dress_pils:
                merged_img.paste(img, (0, y_offset))
                y_offset += img.height
            merged_img.save(dress_img_path, "JPEG")
        elif len(dress_pils) == 1:
            dress_pils[0].save(dress_img_path, "JPEG")
        else:
            raise HTTPException(status_code=400, detail="At least one dress image must be provided.")
            
        # 2. Virtual Try-On ML Call via HuggingFace Space
        # NOTE: Using yisol/IDM-VTON because all CatVTON spaces are currently broken 
        # internally on HuggingFace ("cannot write mode RGBA as JPEG" server error).
        
        # Force reload .env so we don't have to restart the backend server manually
        load_dotenv(override=True)
        hf_token = os.getenv("HF_TOKEN") or settings.HF_TOKEN
        
        client = Client("yisol/IDM-VTON", token=hf_token) if hf_token else Client("yisol/IDM-VTON")
        
        person_dict = {
            "background": handle_file(user_img_path),
            "layers": [],
            "composite": None
        }
        
        # Create a highly detailed strict prompt to enforce preservation of the original garment
        final_garment_des = f"""You are a professional Virtual Try-On AI.

Your task is NOT to generate a new outfit.

Use the uploaded garment image as the ONLY clothing source.

The uploaded garment must be transferred exactly onto the uploaded person's body.

Requirements:

* Preserve the original garment exactly as uploaded.
* Do not change the garment color.
* Do not change the garment texture.
* Do not change the garment pattern.
* Do not change the garment stitching.
* Do not change the garment logo or branding.
* Do not redesign or invent any new clothing details.

The garment should naturally fit the person's body shape, height, shoulder width, waist, arms, and pose.

Maintain realistic:

* Fabric folds
* Cloth wrinkles
* Sleeve alignment
* Collar position
* Hem position
* Shadows
* Lighting
* Perspective
* Body proportions

The clothing should appear as if the person is actually wearing it.

Do not float the clothing.

Do not stretch or compress the garment unnaturally.

Do not distort the body.

The garment must correctly wrap around the body according to the person's pose.

Keep hands, fingers, face, hair, skin tone, background, shoes, and pants unchanged unless they are covered by the uploaded garment.

Generate a realistic, high-quality virtual try-on result with seamless garment fitting.

Occasion:
{occasion}

Garment Category:
{category}

Garment Details:
Gender: {gender}
Color: {color}
Fabric: {fabric}
Pattern: {pattern}
Fit: {fit}
Sleeves: {sleeve}
Style: {style}
"""

        # Run prediction in a thread pool to avoid blocking the async event loop
        result = await run_in_threadpool(
            client.predict,
            dict=person_dict,
            garm_img=handle_file(dress_img_path),
            garment_des=final_garment_des,
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            api_name="/tryon"
        )
        
        generated_img_path = result[0]
        # 3. Cloudinary Uploads with Fallback
        try:
            # Upload user image
            user_upload = cloudinary.uploader.upload(user_img_path)
            user_img_url = user_upload.get("secure_url")
            
            # Upload dress image
            dress_upload = cloudinary.uploader.upload(dress_img_path)
            dress_img_url = dress_upload.get("secure_url")
            
            # Upload generated image
            result_upload = cloudinary.uploader.upload(generated_img_path)
            result_img_url = result_upload.get("secure_url")
        except Exception as upload_err:
            print(f"Cloudinary upload failed: {upload_err}. Falling back to base64.")
            import base64
            with open(user_img_path, "rb") as f:
                user_img_url = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            with open(dress_img_path, "rb") as f:
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary files
        shutil.rmtree(temp_dir)

@router.get("/history")
async def get_tryon_history(decoded_token: dict = Depends(get_current_user)):
    user_id = decoded_token["uid"]
    history = await TryOnHistory.find(TryOnHistory.userId == user_id).sort(-TryOnHistory.createdAt).to_list()
    return history
