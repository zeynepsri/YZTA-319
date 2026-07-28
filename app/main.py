import app.models
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth
from app.routers import receipt  

app = FastAPI(
    title="AI Destekli Kişisel Enflasyon Analiz Platformu API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(receipt.router, prefix="/api/v1/receipts", tags=["Receipts"])

@app.get("/")
async def root():
    return {"message": "YZTA Enflasyon Analizi Backend Sistemine Hoş Geldiniz!"}