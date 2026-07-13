from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    market_name = Column(String, nullable=True)
    receipt_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, nullable=True)
    file_path = Column(String, nullable=False)  
    status = Column(String, default="PENDING")   
    created_at = Column(DateTime(timezone=True), server_default=func.now())