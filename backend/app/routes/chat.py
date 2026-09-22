from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
import uuid
import shutil
from app.models.chat import ChatQueryRequest
from app.services.chat_service import ChatService
from app.adapters.vision import VisionProviderAdapter

router = APIRouter(prefix="/chat", tags=["AI Chat & Agricultural RAG"])

@router.post("/ask")
async def ask_crop_question(req: ChatQueryRequest):
    try:
        result = await ChatService.ask_question(
            farmer_id=req.farmer_id or "farmer-1001",
            question=req.question,
            conversation_id=req.conversation_id,
            language=req.language,
            crop_context=req.crop_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image")
async def analyze_leaf_image_chat(file: UploadFile = File(...), crop_hint: Optional[str] = Form(None)):
    """Uploads crop leaf image and analyzes illness/symptoms using Multimodal AI Vision."""
    try:
        os.makedirs("uploads", exist_ok=True)
        file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analysis = await VisionProviderAdapter.analyze_crop_image(image_path=file_path, filename=file.filename, crop_hint=crop_hint)
        return {"status": "OK", "filename": file.filename, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
