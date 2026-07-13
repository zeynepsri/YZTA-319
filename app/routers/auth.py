from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str


FAKE_USER_DB = {}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterSchema):
    if user_data.email in FAKE_USER_DB:
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kayıtlı!")
    
    
    hashed = hash_password(user_data.password)
    
    
    FAKE_USER_DB[user_data.email] = {
        "id": len(FAKE_USER_DB) + 1,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password_hash": hashed  
    }
    
    return {
        "message": "Kullanıcı başarıyla kaydedildi.",
        "user": {"email": user_data.email, "full_name": user_data.full_name}
    }

@router.post("/login")
async def login(credentials: LoginSchema):
    user = FAKE_USER_DB.get(credentials.email)
    if not user:
        raise HTTPException(status_code=400, detail="Hatalı e-posta veya şifre!")
        
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Hatalı e-posta veya şifre!")
        
   
    access_token = create_access_token(data={"sub": user["email"], "user_id": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
    }