from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.ai_service import ai_service
from backend.schemas import ChatMessage, ChatResponse, ConversationOut, MessageResponse
from backend.security import get_current_user
from database.base import get_db
from database.models import AIConversation, User

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI Finans Asistanı ile sohbet.

    Örnek sorular:
    - Bu ay neden fazla harcadım?
    - Nereden tasarruf edebilirim?
    - En pahalı ürünüm hangisi?
    - Gelecek ay bütçem yeterli olur mu?
    """
    result = ai_service.chat(db, current_user.id, payload.message)

    if not result.get("response"):
        raise HTTPException(status_code=500, detail="AI cevap üretmedi")

    return ChatResponse(
        response=result["response"],
        agent_name=result.get("agent_name", "assistant"),
        memory_context=result.get("memory_context"),
    )


@router.get("/conversations", response_model=list[ConversationOut])
def get_conversations(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sohbet geçmişi."""
    convs = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.created_at.desc())
        .limit(limit)
        .all()
    )
    convs.reverse()
    return [ConversationOut.model_validate(c) for c in convs]


@router.delete("/conversations", response_model=MessageResponse)
def clear_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sohbet geçmişini temizle."""
    db.query(AIConversation).filter(AIConversation.user_id == current_user.id).delete()
    db.commit()
    return MessageResponse(message="Sohbet geçmişi temizlendi")