import httpx
from app.adapters.llm.base import BaseLLMAdapter
from app.config import settings
from typing import Dict, Any, List

class OpenAILLMAdapter(BaseLLMAdapter):
    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        system_instruction = (
            f"You are AgriGo, a friendly, trustworthy agricultural AI assistant for farmers. "
            f"Always reply in {language} unless specified otherwise. Keep sentences simple, practical, "
            f"and avoid hazardous pesticide overdosing. Prioritize integrated pest management (IPM)."
        )
        
        messages = [{"role": "system", "content": system_instruction}]
        for c in context:
            messages.append({"role": "system", "content": f"Agricultural Evidence: {c.get('content', '')}"})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.3}
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "content": content,
                "provider": "OpenAI",
                "model": "gpt-4o-mini",
                "evidence_used": [c.get("title", "Evidence") for c in context]
            }
