from fastapi import APIRouter, HTTPException
from app.models.chat import ChatQueryRequest
from app.services.chat_service import ChatService

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
