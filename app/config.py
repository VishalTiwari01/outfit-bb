from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_EXPIRES_IN: str
    MONGODB_URI: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_CLIENT_EMAIL: str
    FIREBASE_PRIVATE_KEY: str
    
    # Hugging Face (Optional for bypassing rate limits)
    HF_TOKEN: str | None = None

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
