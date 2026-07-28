from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    monthly_budget: Optional[float] = 0.0
    savings_goal: Optional[float] = 0.0


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    monthly_budget: Optional[float] = None
    savings_goal: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    monthly_budget: Optional[float] = None
    savings_goal: Optional[float] = None