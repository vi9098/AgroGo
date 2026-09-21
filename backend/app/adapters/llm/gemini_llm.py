import httpx
from app.adapters.llm.base import BaseLLMAdapter
from app.config import settings
from typing import Dict, Any, List

class GeminiLLMAdapter(BaseLLMAdapter):
    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        evidence_text = "\n".join([f"- {c.get('content', '')}" for c in context])
        full_prompt = (
            f"You are AgriGo AI farming assistant. Reply in {language}.\n"
            f"Context:\n{evidence_text}\n\n"
            f"Farmer Question: {prompt}"
        )
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                url,
                json={"contents": [{"parts": [{"text": full_prompt}]}]}
            )
            res.raise_for_status()
            data = res.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "content": content,
                "provider": "Google Gemini",
                "model": "gemini-1.5-flash",
                "evidence_used": [c.get("title", "Evidence") for c in context]
            }
