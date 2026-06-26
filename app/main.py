from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import auth, wardrobe, rewards, image, history, tryon

app = FastAPI(title="WardrobeAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def start_db():
    await init_db()

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(wardrobe.router, prefix="/api/wardrobe", tags=["Wardrobe"])
app.include_router(rewards.router, prefix="/api/rewards", tags=["Rewards"])
app.include_router(image.router, prefix="/api/image", tags=["Image"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(tryon.router, prefix="/api/tryon", tags=["TryOn"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI WardrobeAI is running"}
