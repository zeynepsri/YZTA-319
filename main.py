from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import ai, analytics, auth, dashboard, inflation, notification, receipt, user
from database.base import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç/bitiş lifecycle."""
    
    Base.metadata.create_all(bind=engine)
    
    _seed_if_empty()
    yield
    


def _seed_if_empty() -> None:
    """Boş veritabanına demo veri ekler."""
    from database.base import SessionLocal
    from database.models import User
    from database.seed import run_seed

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            run_seed()
    except Exception:
        pass
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI Destekli Kişisel Enflasyon Analiz Platformu - Backend API\n\n"
        "## Özellikler\n"
        "- JWT Authentication\n"
        "- Fiş yükleme & OCR\n"
        "- Kişisel enflasyon hesaplama\n"
        "- TÜİK karşılaştırma\n"
        "- AI Finans Asistanı\n"
        "- Dashboard & Analytics\n"
        "- Bildirimler\n"
    ),
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(receipt.router)
app.include_router(dashboard.router)
app.include_router(inflation.router)
app.include_router(ai.router)
app.include_router(notification.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
def root():
    """Health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "healthy"}