import os
import json
import logging
import httpx
from app.adapters.llm.base import BaseLLMAdapter
from app.config import settings
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agrigo.openai")

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class OpenAILLMAdapter(BaseLLMAdapter):
    """
    OpenAI Agricultural Intelligence Adapter (gpt-4o-mini)
    Handles precision crop lifecycle scheduling and conversational farmer query answering.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY", "")

    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "hi") -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        lang_name = "Hindi (हिंदी)" if language == "hi" else ("English" if language == "en" else language)
        system_instruction = (
            f"You are AgriGo, a friendly, authoritative, and practical agricultural AI assistant for Indian farmers. "
            f"Always reply in {lang_name} unless specified otherwise. Keep sentences simple, practical, "
            f"address the farmer as 'किसान भाई' or 'आप', and avoid hazardous pesticide overdosing. Prioritize integrated pest management (IPM)."
        )

        messages = [{"role": "system", "content": system_instruction}]
        for c in context:
            messages.append({"role": "system", "content": f"Agricultural Evidence: {c.get('content', '')}"})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                OPENAI_API_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.3}
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "content": content,
                "provider": "OpenAI (gpt-4o-mini)",
                "model": "gpt-4o-mini",
                "evidence_used": [c.get("title", "Evidence") for c in context]
            }

    async def generate_crop_schedule(
        self,
        crop_name: str,
        sowing_date_str: str,
        acreage: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Uses OpenAI (gpt-4o-mini) to generate a comprehensive agricultural production schedule
        with exact acreage-scaled fertilizer dosages, irrigation timing, and IPM sprays.
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        prompt = (
            f"You are AgriGo's Chief ICAR Agronomist and Crop Scientist.\n"
            f"Farmer Request:\n"
            f"- Crop Name: {crop_name}\n"
            f"- Sowing / Seeding Date: {sowing_date_str} (YYYY-MM-DD)\n"
            f"- Farm Land Area: {acreage} Acres (एकड़)\n\n"
            f"TASK:\n"
            f"Generate a rigorous, complete agricultural production schedule with precise calendar dates, "
            f"phenological stages (01 to 05), irrigation timing, acreage-scaled fertilizer doses (DAP, Urea, MOP in kg), "
            f"and preventative IPM pesticide / fungicide sprays.\n\n"
            f"STRICT RULES:\n"
            f"1. Multiply all per-acre fertilizer requirements by EXACTLY {acreage} acres to output total kilograms needed.\n"
            f"2. Base irrigation intervals on official ICAR/TNAU water requirements from the sowing date.\n"
            f"3. Prioritize organic IPM (Neem oil, sticky traps, Trichoderma) and include safe CIBRC/ICAR chemical dosages.\n"
            f"4. Format stage as '01 - बुवाई व आधार पोषण', '02 - कल्ले / वानस्पतिक', '03 - फूल व फली', '04 - दाना विकास', '05 - परिपक्वता व कटाई'.\n"
            f"5. Output language: Hindi (हिंदी) with English technical terms in parentheses.\n"
            f"6. Return ONLY a single strictly valid JSON object matching this schema:\n"
            f"{{\n"
            f'  "crop_name": "{crop_name}",\n'
            f'  "sowing_date": "{sowing_date_str}",\n'
            f'  "acreage": {acreage},\n'
            f'  "stages": [\n'
            f'    {{"stage_number": "01", "stage_name": "बुवाई व अंकुरण (Sowing & Germination)", "days_from_sowing": 0, "target_date": "YYYY-MM-DD", "description": "..."}},\n'
            f'    {{"stage_number": "02", "stage_name": "...", "days_from_sowing": 21, "target_date": "YYYY-MM-DD", "description": "..."}}\n'
            f'  ],\n'
            f'  "irrigation_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "01 - ...", "description": "...", "priority": "high"}}\n'
            f'  ],\n'
            f'  "fertilizer_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "01 - ...", "dosage_kg": "...", "description": "...", "priority": "high"}}\n'
            f'  ],\n'
            f'  "pesticide_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "01 - ...", "preventative_spray": "...", "dosage": "...", "description": "...", "priority": "normal"}}\n'
            f'  ]\n'
            f"}}"
        )

        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are AgriGo, an elite ICAR Agricultural Scientist. Always respond in valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            if res.status_code == 200:
                raw_data = res.json()
                content_str = raw_data["choices"][0]["message"]["content"]
                parsed = json.loads(content_str)
                parsed["ai_provider"] = "OpenAI (gpt-4o-mini)"
                return parsed
            else:
                err_msg = f"HTTP {res.status_code}: {res.text[:200]}"
                logger.warning(f"[OpenAI Scheduler] API request failed: {err_msg}")
                raise RuntimeError(err_msg)
