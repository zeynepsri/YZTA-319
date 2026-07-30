from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.schemas import DashboardOut, ReceiptOut
from backend.security import get_current_user
from database.base import get_db
from database.models import (
    Category,
    MonthlyInflation,
    OfficialInflation,
    Receipt,
    ReceiptItem,
    Store,
    User,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard verisi - özet, enflasyon, bütçe, son fişler."""
    today = date.today()
    current_month_start = today.replace(day=1)

    # Bu ayki toplam harcama
    total_spending = (
        db.query(func.sum(Receipt.total_amount))
        .filter(
            Receipt.user_id == current_user.id,
            Receipt.receipt_date >= current_month_start,
            Receipt.status == "completed",
        )
        .scalar()
    ) or 0.0

    # Enflasyon verisi
    personal_inflation = None
    official_inflation = None
    inflation_difference = None
    ai_commentary = None

    monthly = (
        db.query(MonthlyInflation)
        .filter(MonthlyInflation.user_id == current_user.id)
        .order_by(MonthlyInflation.month.desc())
        .first()
    )
    if monthly:
        personal_inflation = monthly.personal_rate
        official_inflation = monthly.official_rate
        inflation_difference = monthly.difference
        ai_commentary = monthly.ai_commentary

    # TÜİK verisi (enflasyon kaydı yoksa)
    if official_inflation is None:
        official = db.query(OfficialInflation).order_by(OfficialInflation.month.desc()).first()
        if official:
            official_inflation = official.annual_rate

    # Bütçe
    remaining_budget = None
    budget_usage = None
    if current_user.monthly_budget:
        remaining_budget = current_user.monthly_budget - float(total_spending)
        budget_usage = round((float(total_spending) / current_user.monthly_budget) * 100, 1) if current_user.monthly_budget > 0 else 0

    # Son fişler
    recent_receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == current_user.id, Receipt.status == "completed")
        .order_by(Receipt.created_at.desc())
        .limit(5)
        .all()
    )

    # Kategori bazlı harcama (bu ay)
    category_spending: dict[str, float] = defaultdict(float)
    receipts_this_month = (
        db.query(Receipt)
        .filter(
            Receipt.user_id == current_user.id,
            Receipt.receipt_date >= current_month_start,
            Receipt.status == "completed",
        )
        .all()
    )
    for r in receipts_this_month:
        for item in r.items:
            cat_name = "Diğer"
            if item.product and item.product.category:
                cat_name = item.product.category.name
            category_spending[cat_name] += item.total_price

    # AI önerileri
    ai_suggestions = _generate_suggestions(
        float(total_spending), current_user.monthly_budget, personal_inflation, official_inflation
    )

    return DashboardOut(
        total_spending_this_month=float(total_spending),
        personal_inflation=personal_inflation,
        official_inflation=official_inflation,
        inflation_difference=inflation_difference,
        remaining_budget=remaining_budget,
        budget_usage_percent=budget_usage,
        recent_receipts=[ReceiptOut.model_validate(r) for r in recent_receipts],
        category_spending=dict(category_spending),
        ai_suggestions=ai_suggestions,
        ai_commentary=ai_commentary,
    )


def _generate_suggestions(
    total: float, budget: float | None, personal: float | None, official: float | None
) -> list[str]:
    """Basit kural tabanlı AI önerileri."""
    suggestions: list[str] = []

    if budget and total > budget * 0.8:
        suggestions.append("⚠️ Bu ay bütçenin %80'ini aştın. Harcamalarını kontrol altına al.")
    elif budget and total < budget * 0.5:
        suggestions.append("✅ Harika gidiyorsun! Bütçenin yarısını kullandın, tasarruf hedefine yaklaşıyorsun.")

    if personal and official and personal > official:
        diff = round(personal - official, 1)
        suggestions.append(f"📊 Kişisel enflasyonun TÜİK'ten %{diff} yüksek. Gıda harcamalarını gözden geçir.")

    if not suggestions:
        suggestions.append("💡 Daha fazla analiz için fiş yüklemeye devam et.")

    return suggestions