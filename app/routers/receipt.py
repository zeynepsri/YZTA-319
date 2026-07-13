from fastapi import APIRouter, UploadFile, File, HTTPException, status
import os
from datetime import datetime

router = APIRouter(prefix="/receipt", tags=["Receipt"])

UPLOAD_DIR = "uploaded_receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Emircan veritabanını bağlayana kadar yüklenen fişleri tutacağımız geçici hafıza (Mock DB)
FAKE_RECEIPT_DB = {}
receipt_id_counter = 1

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    user_id: int,  
    file: UploadFile = File(...)
):
    global receipt_id_counter
    
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(
            status_code=400, 
            detail="Geçersiz dosya formatı! Sadece JPG, PNG veya PDF yüklenebilir."
        )
        
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"user_{user_id}_{timestamp}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception:
        raise HTTPException(status_code=500, detail="Dosya sunucuya kaydedilirken bir hata oluştu.")
        
   
    receipt_record = {
        "id": receipt_id_counter,
        "user_id": user_id,
        "market_name": None,      
        "receipt_date": None,     
        "total_amount": None,     
        "file_path": file_path,
        "status": "PENDING",       
        "created_at": datetime.now().isoformat()
    }
    
    FAKE_RECEIPT_DB[receipt_id_counter] = receipt_record
    receipt_id_counter += 1
    
    return {
        "message": "Fiş başarıyla yüklendi ve işleme sırasına alındı (PENDING).",
        "receipt": receipt_record
    }

# Test 
@router.get("/list")
async def list_receipts():
    return list(FAKE_RECEIPT_DB.values())