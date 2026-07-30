from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import MessageResponse, UserOut, UserUpdate
from database.base import get_db
from database.models import User, UserGoal
from backend.security import get_current_user

router = APIRouter(prefix="/user", tags=["User"])


@router.get("", response_model=UserOut)
def get_user(current_user: User = Depends(get_current_user)):
    """Kullanıcı profil bilgisi."""
    return UserOut.model_validate(current_user)


@router.put("", response_model=UserOut)
def update_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Profil güncelleme."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.monthly_budget is not None:
        current_user.monthly_budget = payload.monthly_budget
        # Hedef olarak da kaydet
        goal = db.query(UserGoal).filter(
            UserGoal.user_id == current_user.id,
            UserGoal.goal_type == "budget",
            UserGoal.is_active == True,
        ).first()
        if goal:
            goal.target_value = payload.monthly_budget
        else:
            db.add(UserGoal(user_id=current_user.id, goal_type="budget", target_value=payload.monthly_budget))
    if payload.savings_goal is not None:
        current_user.savings_goal = payload.savings_goal
        goal = db.query(UserGoal).filter(
            UserGoal.user_id == current_user.id,
            UserGoal.goal_type == "savings",
            UserGoal.is_active == True,
        ).first()
        if goal:
            goal.target_value = payload.savings_goal
        else:
            db.add(UserGoal(user_id=current_user.id, goal_type="savings", target_value=payload.savings_goal))
    if payload.preferred_currency is not None:
        current_user.preferred_currency = payload.preferred_currency

    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)