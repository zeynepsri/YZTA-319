from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.ai_service import ai_service
from backend.config import settings
from backend.schemas import MessageResponse, ReceiptOut, ReceiptUploadResponse
from backend.security import get_current_user
from database.base import get_db
from database.models import Notification, Receipt, User

router = APIRouter(prefix="/receipt", tags=["Receipt"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fiş yükleme - dosya alır, AI'a gönderir, sonucu kaydeder."""
    
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen dosya türü. İzin verilenler: {ALLOWED_EXTENSIONS}")

    
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Dosya çok büyük (max {settings.MAX_FILE_SIZE_MB}MB)")

    
    file_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(content)

    file_type = "pdf" if ext == ".pdf" else "image"

    
    receipt = Receipt(
        user_id=current_user.id,
        file_url=file_path,
        file_type=file_type,
        status="processing",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    
    result = ai_service.process_receipt_image(db, receipt.id, file_path)

    if "error" in result:
        return ReceiptUploadResponse(
            receipt_id=receipt.id,
            status="failed",
            message=f"AI işleme hatası: {result['error']}",
        )

    
    db.add(
        Notification(
            user_id=current_user.id,
            title="Fiş işlendi",
            body=f"Fişiniz başarıyla işlendi. Toplam: {result.get('receipt', {}).get('total', 0)} TL",
            notification_type="ocr_completed",
        )
    )
    db.commit()

    return ReceiptUploadResponse(
        receipt_id=receipt.id,
        status="completed",
        message="Fiş başarıyla işlendi",
        ai_result=result.get("receipt"),
    )


@router.post("/upload-text", response_model=ReceiptUploadResponse)
def upload_receipt_text(
    raw_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """OCR metni yükleme - metin alır, AI'a gönderir."""
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Boş metin")

    receipt = Receipt(
        user_id=current_user.id,
        ocr_raw_text=raw_text,
        status="processing",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    result = ai_service.process_receipt_text(db, receipt.id, raw_text)

    if "error" in result:
        return ReceiptUploadResponse(
            receipt_id=receipt.id,
            status="failed",
            message=f"AI işleme hatası: {result['error']}",
        )

    db.add(
        Notification(
            user_id=current_user.id,
            title="Fiş işlendi",
            body=f"Fişiniz başarıyla işlendi. Toplam: {result.get('receipt', {}).get('total', 0)} TL",
            notification_type="ocr_completed",
        )
    )
    db.commit()

    return ReceiptUploadResponse(
        receipt_id=receipt.id,
        status="completed",
        message="Fiş başarıyla işlendi",
        ai_result=result.get("receipt"),
    )


@router.get("", response_model=list[ReceiptOut])
def list_receipts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fiş listeleme (sayfalama)."""
    receipts = (
        db.query(Receipt)
        .filter(Receipt.user_id == current_user.id)
        .order_by(Receipt.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ReceiptOut.model_validate(r) for r in receipts]


@router.get("/{receipt_id}", response_model=ReceiptOut)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek fiş detayı."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == current_user.id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Fiş bulunamadı")
    return ReceiptOut.model_validate(receipt)


@router.delete("/{receipt_id}", response_model=MessageResponse)
def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fiş silme."""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == current_user.id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Fiş bulunamadı")

    
    if receipt.file_url and os.path.exists(receipt.file_url):
        try:
            os.remove(receipt.file_url)
        except OSError:
            pass

    db.delete(receipt)
    db.commit()
    return MessageResponse(message="Fiş silindi")