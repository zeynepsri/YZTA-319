from fastapi import APIRouter, UploadFile, File
import os

router = APIRouter(prefix="/receipt", tags=["Receipt"])

UPLOAD_DIR = "uploaded_receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        return {"error": "Sadece JPG, PNG veya PDF yüklenebilir!"}
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    return {
        "message": "Fiş başarıyla yüklendi ve sunucuya kaydedildi.",
        "filename": file.filename,
        "saved_path": file_path
    }
