import os

folders = [
    "app",
    "app/core",
    "app/models",
    "app/schemas",
    "app/routers",
    "app/services",
]

files = {
    "app/__init__.py": "",
    "app/main.py": """from fastapi import FastAPI
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
""",
    "app/core/config.py": """import os

class Settings:
    PROJECT_NAME: str = "YZTA Enflasyon Analizi"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_CHANGEME_123456")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 Gün
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/yzta_db")

settings = Settings()
""",
    "app/core/database.py": """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
""",
    "app/core/security.py": """from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
""",
    "app/models/__init__.py": "# Emircan DB modellerini buraya ekleyecek",
    "app/schemas/__init__.py": "# Pydantic şemaları burada toplanacak",
    "app/routers/__init__.py": "",
    "app/routers/auth.py": """from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(user_data: RegisterSchema):
    return {"message": "Kullanıcı başarıyla kaydedildi (Sprint 1 Mock)", "user": user_data.email}

@router.post("/login")
async def login(credentials: LoginSchema):
    if credentials.email == "test@yzta.com" and credentials.password == "123456":
        return {"access_token": "mock_token_123456", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Hatalı e-posta veya şifre")

@router.post("/logout")
async def logout():
    return {"message": "Başarıyla çıkış yapıldı"}
""",
    "app/routers/receipt.py": """from fastapi import APIRouter, UploadFile, File
import os

router = APIRouter(prefix="/receipt", tags=["Receipt"])

UPLOAD_DIR = "uploaded_receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        return {"error": "Sadece JPG, PNG veya PDF yüklenebilir!"}
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    return {
        "message": "Fiş başarıyla yüklendi ve sunucuya kaydedildi.",
        "filename": file.filename,
        "saved_path": file_path
    }
""",
    "app/services/__init__.py": ""
}

print("YZTA Proje iskeleti oluşturuluyor")

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for file_path, content in files.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("\nKlasörler ve temel dosyalar oluşturuldu")