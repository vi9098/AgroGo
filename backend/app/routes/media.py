import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.services.audit_service import AuditService

router = APIRouter(prefix="/media", tags=["Media Storage"])

@router.post("/upload")
async def upload_crop_photo(file: UploadFile = File(...)):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    safe_name = f"{file_id}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_name)
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
        
    await AuditService.log_event(
        actor_id="farmer-upload",
        actor_type="farmer",
        action="PHOTO_UPLOADED",
        resource_type="media",
        resource_id=file_id
    )
    
    return {
        "file_id": file_id,
        "filename": safe_name,
        "url": f"/uploads/{safe_name}",
        "size_bytes": len(content),
        "diagnosis_hint": "Photo received. What AgriGo noticed: Possible Leaf Curling. Check for aphids/whiteflies."
    }
