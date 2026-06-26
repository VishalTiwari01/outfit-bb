from fastapi import APIRouter, UploadFile, File, Response
import io
import traceback

router = APIRouter()

@router.post("/remove-bg")
async def remove_background(image: UploadFile = File(...)):
    try:
        from rembg import remove
        input_image = await image.read()
        output_image = remove(input_image)
        return Response(content=output_image, media_type="image/png")
    except Exception as e:
        print(f"Error in remove_background: {e}")
        traceback.print_exc()
        return Response(status_code=500, content=f"Failed to remove background: {str(e)}")
