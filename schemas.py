from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict



class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshTokenRequest(BaseModel):
    refresh_token: str



class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    monthly_budget: Optional[float] = None
    savings_goal: Optional[float] = None
    preferred_currency: str = "TRY"
    is_verified: bool = False
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    monthly_budget: Optional[float] = None
    savings_goal: Optional[float] = None
    preferred_currency: Optional[str] = None



class ReceiptItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_name: str
    product_id: Optional[int] = None
    quantity: float
    unit_price: float
    total_price: float
    confidence: float


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: Optional[int] = None
    receipt_date: Optional[date] = None
    total_amount: Optional[float] = None
    currency: str = "TRY"
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    ocr_confidence: Optional[float] = None
    status: str = "pending"
    created_at: datetime
    processed_at: Optional[datetime] = None
    items: list[ReceiptItemOut] = []


class ReceiptUploadResponse(BaseModel):
    receipt_id: int
    status: str
    message: str
    ai_result: Optional[dict[str, Any]] = None



class InflationOut(BaseModel):
    id: int
    month: date
    personal_rate: float
    official_rate: Optional[float] = None
    difference: Optional[float] = None
    category_breakdown: Optional[dict[str, Any]] = None
    ai_commentary: Optional[str] = None
    created_at: datetime


class InflationHistoryItem(BaseModel):
    month: date
    personal_rate: float
    official_rate: Optional[float] = None
    difference: Optional[float] = None



class DashboardOut(BaseModel):
    total_spending_this_month: float
    personal_inflation: Optional[float] = None
    official_inflation: Optional[float] = None
    inflation_difference: Optional[float] = None
    remaining_budget: Optional[float] = None
    budget_usage_percent: Optional[float] = None
    recent_receipts: list[ReceiptOut] = []
    category_spending: dict[str, float] = {}
    ai_suggestions: list[str] = []
    ai_commentary: Optional[str] = None



class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    response: str
    agent_name: str = "assistant"
    memory_context: Optional[dict[str, Any]] = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    agent_name: Optional[str] = None
    created_at: datetime



class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    notification_type: str
    is_read: bool = False
    created_at: datetime



class AnalyticsOut(BaseModel):
    monthly_spending: list[dict[str, Any]] = []
    category_distribution: dict[str, float] = {}
    store_comparison: dict[str, float] = {}
    top_products: list[dict[str, Any]] = []
    most_inflated_products: list[dict[str, Any]] = []



class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20



TokenResponse.model_rebuild()