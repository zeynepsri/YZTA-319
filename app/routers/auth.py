from fastapi import APIRouter, Depends, HTTPException, status
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
