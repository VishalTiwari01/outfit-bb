import os
import json
from google import genai
from google.genai import types
from app.models.wardrobe import WardrobeItemCreate

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def analyze_clothing_image(image_url: str) -> dict:
    """
    Downloads an image (if needed) or passes URL to Gemini,
    then returns structured JSON metadata about the clothing item.
    """
    if not client:
        print("WARNING: GEMINI_API_KEY not set. Returning dummy AI data.")
        return get_dummy_metadata(image_url)

    prompt = """
    You are an expert fashion AI. Analyze this clothing item and return a JSON object with the following schema perfectly formatted.
    Be as accurate and descriptive as possible.
    
    Fields required:
    - category (Top, Bottom, Footwear, One Piece, Accessory)
    - subcategory (e.g. Formal Shirt, T-Shirt, Jeans, Trousers, Oxford Shoes, Sneakers)
    - colors (object with "primary" and "secondary" hex or name)
    - pattern (Solid, Striped, Checkered, Floral, etc.)
    - material (Cotton, Leather, Denim, Silk, etc.)
    - fabric (Broadcloth, Oxford, etc.)
    - texture (Smooth, Rough, Ribbed)
    - transparency (Opaque, Sheer)
    - fit (Slim, Regular, Oversized)
    - length (Short, Full, Cropped)
    - neck (Collar, Crew, V-Neck)
    - collarType (Button-down, Spread, Mandarin)
    - sleeve (Full, Half, Sleeveless)
    - pocketCount (integer)
    - buttonType (Metal, Plastic, None)
    - closureType (Zipper, Button, Pullover)
    - printType (None, Graphic, All-over)
    - layerType (Base, Outer, Mid)
    - brand (Guess if clear, else null)
    - logoPresent (boolean)
    - style (Minimal, Streetwear, Preppy, etc.)
    - fashionStyle (Vintage, Modern, Classic)
    - dressCode (Casual, Smart Casual, Formal, Black Tie)
    - season (Array: Summer, Winter, Spring, Autumn)
    - occasion (Array: Office, Party, Travel, Wedding, Casual)
    - ageGroup (Adult, Teen, Kid)
    - gender (Male, Female, Unisex)
    - weatherScore (0.0 to 1.0, 1.0 being hottest weather)
    - luxuryScore (0.0 to 1.0, 1.0 being highest luxury)
    - casualScore (0.0 to 1.0, 1.0 being most casual)
    - formalityScore (0.0 to 1.0, 1.0 being most formal)
    - confidence (0.0 to 1.0, how confident you are in this analysis)
    """

    try:
        # Check if the image is base64 encoded
        import base64
        if image_url.startswith("data:image"):
            # Extract the base64 part: "data:image/png;base64,iVBORw..."
            base64_str = image_url.split(",")[1]
            image_bytes = base64.b64decode(base64_str)
            mime_type = image_url.split(";")[0].split(":")[1]
        else:
            # We need to fetch the image from URL
            import httpx
            response = httpx.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
            mime_type = 'image/jpeg'
        
        # Call Gemini Vision (gemini-2.5-flash)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        ai_data = json.loads(response.text)
        return ai_data
    except Exception as e:
        print(f"Error in Gemini Vision API: {e}")
        return get_dummy_metadata(image_url)

def generate_clothing_embedding(ai_data: dict) -> list[float]:
    """
    Generates a 768-dimensional vector embedding based on the item's metadata.
    """
    if not client:
        return [0.0] * 768
        
    try:
        # Create a rich text description to embed
        description = f"Category: {ai_data.get('category')} - {ai_data.get('subcategory')}. "
        description += f"Color: {ai_data.get('colors', {}).get('primary', '')}. "
        description += f"Style: {ai_data.get('style')}, {ai_data.get('dressCode')}. "
        description += f"Occasions: {', '.join(ai_data.get('occasion', []))}. "
        description += f"Material: {ai_data.get('material')}. "
        
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=description
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Error in Gemini Embedding API: {e}")
        return [0.0] * 768

def process_wardrobe_upload(image_url: str, title: str = "") -> dict:
    """
    Main pipeline: 1. Extract Metadata -> 2. Generate Embedding
    """
    metadata = analyze_clothing_image(image_url)
    embedding = generate_clothing_embedding(metadata)
    
    metadata["embedding"] = embedding
    metadata["imageUrl"] = image_url
    metadata["title"] = title or f"{metadata.get('colors', {}).get('primary', '')} {metadata.get('subcategory', 'Item')}"
    
    return metadata

def get_dummy_metadata(image_url: str) -> dict:
    """Fallback if API fails or no key is provided."""
    return {
        "category": "Top",
        "subcategory": "T-Shirt",
        "colors": {"primary": "White", "secondary": "None"},
        "pattern": "Solid",
        "material": "Cotton",
        "fit": "Regular",
        "neck": "Crew",
        "sleeve": "Half",
        "style": "Minimal",
        "season": ["Summer", "Spring"],
        "occasion": ["Casual", "Travel"],
        "confidence": 0.95,
        "embedding": [0.0] * 768
    }
