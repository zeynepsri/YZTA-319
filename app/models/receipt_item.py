from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    item_name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    quantity = Column(Integer, default=1)

    receipt = relationship("Receipt", back_populates="items")