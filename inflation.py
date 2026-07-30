from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.ai_service import ai_service
from backend.schemas import InflationHistoryItem, InflationOut, MessageResponse
from backend.security import get_current_user
from database.base import get_db
from database.models import MonthlyInflation, Notification, User

router = APIRouter(prefix="/inflation", tags=["Inflation"])


@router.get("", response_model=InflationOut | None)
def get_current_inflation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """En güncel kişisel enflasyon oranı."""
    monthly = (
        db.query(MonthlyInflation)
        .filter(MonthlyInflation.user_id == current_user.id)
        .order_by(MonthlyInflation.month.desc())
        .first()
    )
    if not monthly:
        return None
    return InflationOut(
        id=monthly.id,
        month=monthly.month,
        personal_rate=monthly.personal_rate,
        official_rate=monthly.official_rate,
        difference=monthly.difference,
        category_breakdown=monthly.category_breakdown,
        ai_commentary=monthly.ai_commentary,
        created_at=monthly.created_at,
    )


@router.get("/history", response_model=list[InflationHistoryItem])
def get_inflation_history(
    limit: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enflasyon geçmişi."""
    records = (
        db.query(MonthlyInflation)
        .filter(MonthlyInflation.user_id == current_user.id)
        .order_by(MonthlyInflation.month.desc())
        .limit(limit)
        .all()
    )
    return [
        InflationHistoryItem(
            month=r.month,
            personal_rate=r.personal_rate,
            official_rate=r.official_rate,
            difference=r.difference,
        )
        for r in records
    ]


@router.post("/recalculate")
def recalculate_inflation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kişisel enflasyonu yeniden hesapla (AI Agent'ı tetikler)."""
    result = ai_service.calculate_inflation(db, current_user.id)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Bildirim
    db.add(
        Notification(
            user_id=current_user.id,
            title="Enflasyon analizi hazır",
            body=f"Kişisel enflasyonun %{result.get('personal_rate', 0):.1f} olarak hesaplandı.",
            notification_type="analysis_ready",
        )
    )
    db.commit()

    return result