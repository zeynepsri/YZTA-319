from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from ai_agents.orchestrator import orchestrator
from database.models import (
    AIConversation,
    Category,
    OfficialInflation,
    PriceHistory,
    Product,
    Receipt,
    ReceiptItem,
    Store,
    User,
    UserGoal,
    UserMemory,
)


class AIIntegrationService:
    """Backend <-> AI Agent iletişim katmanı."""

    def __init__(self) -> None:
        self.orchestrator = orchestrator

   
    def process_receipt_image(self, db: Session, receipt_id: int, image_path: str) -> dict[str, Any]:
        """Fiş görüntüsünü AI'a gönderir, sonucu DB'ye kaydeder."""
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            return {"error": "Fiş bulunamadı"}

        
        result = self.orchestrator.process_receipt_image(image_path)

        if result.errors:
            receipt.status = "failed"
            receipt.ai_metadata = {"errors": result.errors}
            db.commit()
            return {"error": "; ".join(result.errors)}

        if not result.receipt:
            receipt.status = "failed"
            db.commit()
            return {"error": "AI fiş analiz edemedi"}

        receipt_data = result.receipt

        
        store = self._get_or_create_store(db, receipt_data.store)

        
        receipt.store_id = store.id
        receipt.status = "completed"
        receipt.ocr_confidence = receipt_data.overall_confidence
        receipt.ocr_raw_text = receipt_data.raw_text
        receipt.processed_at = datetime.now()
        if receipt_data.date:
            try:
                receipt.receipt_date = date.fromisoformat(receipt_data.date)
            except ValueError:
                pass
        receipt.total_amount = receipt_data.total
        receipt.ai_metadata = receipt_data.to_dict()

        
        for item in receipt_data.items:
            
            product = self._get_or_create_product(db, item.name, item.category)
            db.add(
                ReceiptItem(
                    receipt_id=receipt.id,
                    product_id=product.id if product else None,
                    raw_name=item.name,
                    quantity=item.quantity,
                    unit_price=item.price,
                    total_price=round(item.price * item.quantity, 2),
                    confidence=item.confidence,
                )
            )
            
            if product and receipt.receipt_date:
                self._add_price_history(db, product.id, store.id, item.price, receipt.receipt_date)

        db.commit()
        return {"receipt": receipt_data.to_dict(), "receipt_id": receipt.id}

    def process_receipt_text(self, db: Session, receipt_id: int, raw_text: str) -> dict[str, Any]:
        """OCR metnini AI'a gönderir."""
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not receipt:
            return {"error": "Fiş bulunamadı"}

        result = self.orchestrator.process_receipt_text(raw_text)

        if result.errors:
            receipt.status = "failed"
            db.commit()
            return {"error": "; ".join(result.errors)}

        receipt_data = result.receipt
        store = self._get_or_create_store(db, receipt_data.store)

        receipt.store_id = store.id
        receipt.status = "completed"
        receipt.ocr_confidence = receipt_data.overall_confidence
        receipt.ocr_raw_text = raw_text
        receipt.processed_at = datetime.now()
        if receipt_data.date:
            try:
                receipt.receipt_date = date.fromisoformat(receipt_data.date)
            except ValueError:
                pass
        receipt.total_amount = receipt_data.total
        receipt.ai_metadata = receipt_data.to_dict()

        for item in receipt_data.items:
            product = self._get_or_create_product(db, item.name, item.category)
            db.add(
                ReceiptItem(
                    receipt_id=receipt.id,
                    product_id=product.id if product else None,
                    raw_name=item.name,
                    quantity=item.quantity,
                    unit_price=item.price,
                    total_price=round(item.price * item.quantity, 2),
                    confidence=item.confidence,
                )
            )
            if product and receipt.receipt_date:
                self._add_price_history(db, product.id, store.id, item.price, receipt.receipt_date)

        db.commit()
        return {"receipt": receipt_data.to_dict(), "receipt_id": receipt.id}

    
    def calculate_inflation(self, db: Session, user_id: int) -> dict[str, Any]:
        """Kullanıcının kişisel enflasyonunu hesaplar ve DB'ye kaydeder."""
        from database.models import MonthlyInflation

        
        spending = self._collect_user_spending(db, user_id)

        
        official = self._get_latest_official(db)

        
        result = self.orchestrator.calculate_inflation(spending, official)

        if result.errors:
            return {"error": "; ".join(result.errors)}

        if not result.inflation:
            return {"error": "Enflasyon hesaplanamadı"}

        inf = result.inflation
        current_month = date.today().replace(day=1)

        # DB'ye kaydet (upsert)
        existing = db.query(MonthlyInflation).filter(
            MonthlyInflation.user_id == user_id, MonthlyInflation.month == current_month
        ).first()

        breakdown_dict = {
            k: {"rate": v.rate, "weight": v.weight} for k, v in inf.category_breakdown.items()
        }

        if existing:
            existing.personal_rate = inf.personal_rate
            existing.official_rate = inf.official_rate
            existing.difference = inf.difference
            existing.category_breakdown = breakdown_dict
            existing.ai_commentary = inf.commentary
        else:
            db.add(
                MonthlyInflation(
                    user_id=user_id,
                    month=current_month,
                    personal_rate=inf.personal_rate,
                    official_rate=inf.official_rate,
                    difference=inf.difference,
                    category_breakdown=breakdown_dict,
                    ai_commentary=inf.commentary,
                )
            )
        db.commit()
        return inf.to_dict()

    
    def chat(self, db: Session, user_id: int, message: str) -> dict[str, Any]:
        """AI Finans Asistanı sohbeti."""
       
        memories = self._get_user_memories(db, user_id)
        goals = self._get_user_goals(db, user_id)
        conversations = self._get_recent_conversations(db, user_id)
        spending_summary = self._get_spending_summary(db, user_id)

        
        result = self.orchestrator.chat(
            user_query=message,
            user_memories=memories,
            user_goals=goals,
            recent_conversations=conversations,
            spending_summary=spending_summary,
        )

        
        db.add(AIConversation(user_id=user_id, role="user", content=message))
        db.add(
            AIConversation(
                user_id=user_id,
                role="assistant",
                content=result.chat_response or "",
                agent_name="assistant",
            )
        )

        
        if result.memory_context:
            for mem in result.memory_context.relevant_memories:
                
                pass

        db.commit()

        return {
            "response": result.chat_response,
            "agent_name": "assistant",
            "memory_context": result.memory_context.to_dict() if result.memory_context else None,
        }

   
    def _get_or_create_store(self, db: Session, store_name: str) -> Store:
        normalized = store_name.upper().strip()
        store = db.query(Store).filter(Store.normalized_name == normalized).first()
        if not store:
            store = Store(name=store_name, normalized_name=normalized)
            db.add(store)
            db.flush()
        return store

    def _get_or_create_product(self, db: Session, name: str, category_name: str) -> Optional[Product]:
        normalized = name.lower().strip()
        product = db.query(Product).filter(Product.normalized_name == normalized).first()
        if not product:
            
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                db.add(category)
                db.flush()
            product = Product(name=name, normalized_name=normalized, category_id=category.id)
            db.add(product)
            db.flush()
        return product

    def _add_price_history(self, db: Session, product_id: int, store_id: int, price: float, recorded_date: date) -> None:
        existing = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id,
            PriceHistory.store_id == store_id,
            PriceHistory.recorded_date == recorded_date,
        ).first()
        if not existing:
            db.add(PriceHistory(product_id=product_id, store_id=store_id, price=price, recorded_date=recorded_date))

    def _collect_user_spending(self, db: Session, user_id: int) -> list[dict[str, Any]]:
        """Kullanıcının son aylardaki harcamasını AI formatında toplar."""
        receipts = (
            db.query(Receipt)
            .filter(Receipt.user_id == user_id, Receipt.status == "completed")
            .order_by(Receipt.receipt_date.desc())
            .limit(100)
            .all()
        )
        spending: list[dict[str, Any]] = []
        for r in receipts:
            if not r.receipt_date:
                continue
            month = r.receipt_date.strftime("%Y-%m")
            for item in r.items:
                product = item.product
                category_name = "Temel Gıda"
                if product and product.category:
                    category_name = product.category.name
                spending.append(
                    {
                        "product": item.raw_name,
                        "category": category_name,
                        "quantity": item.quantity,
                        "price": item.unit_price,
                        "month": month,
                    }
                )
        return spending

    def _get_latest_official(self, db: Session) -> Optional[dict[str, Any]]:
        """En son TÜİK verisini getirir."""
        official = db.query(OfficialInflation).order_by(OfficialInflation.month.desc()).first()
        if not official:
            return None
        return {
            "annual_rate": official.annual_rate,
            "monthly_rate": official.monthly_rate,
            "category_rates": official.category_rates or {},
        }

    def _get_user_memories(self, db: Session, user_id: int) -> list[dict[str, Any]]:
        memories = db.query(UserMemory).filter(UserMemory.user_id == user_id, UserMemory.is_active == True).all()
        return [{"memory_type": m.memory_type, "content": m.content, "importance": m.importance} for m in memories]

    def _get_user_goals(self, db: Session, user_id: int) -> list[dict[str, Any]]:
        goals = db.query(UserGoal).filter(UserGoal.user_id == user_id, UserGoal.is_active == True).all()
        return [{"goal_type": g.goal_type, "target_value": g.target_value, "period": g.period} for g in goals]

    def _get_recent_conversations(self, db: Session, user_id: int) -> list[dict[str, Any]]:
        convs = (
            db.query(AIConversation)
            .filter(AIConversation.user_id == user_id)
            .order_by(AIConversation.created_at.desc())
            .limit(10)
            .all()
        )
        convs.reverse()
        return [{"role": c.role, "content": c.content} for c in convs]

    def _get_spending_summary(self, db: Session, user_id: int) -> dict[str, Any]:
        """Kullanıcının harcama özeti."""
        from sqlalchemy import func

        current_month = date.today().replace(day=1)
        total = (
            db.query(func.sum(Receipt.total_amount))
            .filter(Receipt.user_id == user_id, Receipt.receipt_date >= current_month)
            .scalar()
        ) or 0.0

        user = db.query(User).filter(User.id == user_id).first()
        return {
            "this_month_total": float(total),
            "monthly_budget": user.monthly_budget if user else None,
            "savings_goal": user.savings_goal if user else None,
        }


ai_service = AIIntegrationService()