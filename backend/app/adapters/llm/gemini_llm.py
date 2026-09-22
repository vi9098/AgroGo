import asyncio
import httpx
from app.adapters.llm.base import BaseLLMAdapter
from app.config import settings
from typing import Dict, Any, List

class GeminiLLMAdapter(BaseLLMAdapter):
    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "hi") -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
        
        evidence_text = "\n".join([f"- {c.get('content', '')}" for c in context]) if context else "No extra evidence chunks required."
        lang_name = "Hindi (हिंदी)" if language == "hi" else ("English" if language == "en" else language)
        
        full_prompt = (
            f"You are AgriGo, an authoritative, friendly, highly practical Indian Agricultural AI Assistant for farmers.\n"
            f"Always reply in {lang_name}. Use simple, clear, and actionable language that farmers can immediately understand.\n"
            f"Guidelines:\n"
            f"1. Directly address the farmer's specific question with proven agronomic science.\n"
            f"2. Give concrete steps: seed rate, irrigation timing, fertilizer dosage (Urea, DAP, MOP), or pest control.\n"
            f"3. Prioritize Integrated Pest Management (IPM) & organic remedies (Neem oil, Trichoderma) first.\n"
            f"4. If recommending chemicals, cite safe ICAR/CIBRC dosages per liter of water.\n"
            f"5. Maintain an encouraging, respectful tone (use 'आप', 'किसान भाई').\n"
            f"6. Be direct, practical, and structured in concise bullet points (under 250 words) so farmers can take fast action.\n\n"
            f"Agricultural Scientific Evidence:\n{evidence_text}\n\n"
            f"Farmer's Question: {prompt}\n\n"
            f"AgriGo Practical Advice:"
        )
        
        candidate_models = ["gemini-3.5-flash", "gemini-3.6-flash"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            last_err = None
            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                for attempt in range(2):
                    try:
                        res = await client.post(
                            url,
                            json={
                                "contents": [{"parts": [{"text": full_prompt}]}],
                                "generationConfig": {
                                    "maxOutputTokens": 700,
                                    "temperature": 0.3
                                }
                            }
                        )
                        if res.status_code == 200:
                            data = res.json()
                            content = data["candidates"][0]["content"]["parts"][0]["text"]
                            return {
                                "content": content,
                                "provider": f"Google Gemini ({model_name})",
                                "model": model_name,
                                "evidence_used": [c.get("title", "ICAR Guidelines") for c in context] if context else ["ICAR / TNAU / FAO Agricultural Knowledge Base"]
                            }
                        elif res.status_code in (503, 429):
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            last_err = f"HTTP {res.status_code}: {res.text[:150]}"
                            break
                    except Exception as e:
                        last_err = str(e)
                        await asyncio.sleep(0.5)
                        
            raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")
