from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.core.database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    image_url = Column(Text, nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    receipt_date = Column(Date, nullable=True)
    ocr_confidence = Column(Numeric(4, 3), nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # İlişkiler
    owner = relationship("User", back_populates="receipts")
    store = relationship("Store", back_populates="receipts")
    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")