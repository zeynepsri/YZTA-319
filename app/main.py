from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, receipt

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

app.include_router(auth.router)
app.include_router(receipt.router)

@app.get("/")
async def root():
    return {"message": "YZTA Enflasyon Analizi Backend Sistemine Hoş Geldiniz!"}
