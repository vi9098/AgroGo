from fastapi import APIRouter, UploadFile, File
from app.adapters.fallback import fallback_orchestrator
from app.services.chat_service import ChatService

router = APIRouter(prefix="/voice", tags=["Voice Pipeline"])

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    stt_res = await fallback_orchestrator.transcribe_voice(audio_bytes, file.filename)
    
    # Run through Agricultural AI
    ai_res = await ChatService.ask_question(
        farmer_id="farmer-voice",
        question=stt_res["transcript"],
        language=stt_res["language"]
    )
    
    # Generate Voice Response
    tts_res = await fallback_orchestrator.synthesize_voice(ai_res["response"], stt_res["language"])
    
    return {
        "transcript": stt_res["transcript"],
        "language": stt_res["language"],
        "answer_text": ai_res["response"],
        "audio_url": tts_res["audio_url"],
        "provider": ai_res["provider"]
    }
