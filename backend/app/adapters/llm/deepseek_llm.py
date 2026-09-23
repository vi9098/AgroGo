import os
import httpx
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger("agrigo.deepseek")

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

class DeepSeekLLMAdapter:
    """
    DeepSeek Agricultural AI Intelligence Adapter
    Generates precision crop phenology, acreage-scaled nutrient dosage,
    and stage-based irrigation and IPM pesticide schedules.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY", "")

    async def generate_crop_schedule(
        self,
        crop_name: str,
        sowing_date_str: str,
        acreage: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Uses DeepSeek Chat API to calculate full lifecycle farming timeline with exact acreage dosages.
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")

        prompt = (
            f"You are AgriGo's Chief ICAR Agronomist and Crop Scientist.\n"
            f"Farmer Request:\n"
            f"- Crop Name: {crop_name}\n"
            f"- Sowing / Seeding Date: {sowing_date_str} (YYYY-MM-DD)\n"
            f"- Farm Land Area: {acreage} Acres (एकड़)\n\n"
            f"TASK:\n"
            f"Generate a rigorous, complete agricultural production schedule with precise calendar dates, "
            f"phenological stages, irrigation timing, acreage-scaled fertilizer doses (DAP, Urea, MOP in kg), "
            f"and preventative IPM pesticide / fungicide sprays.\n\n"
            f"STRICT RULES:\n"
            f"1. Multiply all per-acre fertilizer requirements by EXACTLY {acreage} acres to output total kilograms needed.\n"
            f"2. Base irrigation intervals on official ICAR/TNAU water requirements from the sowing date.\n"
            f"3. Prioritize organic IPM (Neem oil, sticky traps, Trichoderma) and include safe CIBRC/ICAR chemical dosages.\n"
            f"4. Output language: Hindi (हिंदी) with English technical terms in parentheses.\n"
            f"5. Return ONLY a single strictly valid JSON object matching this schema:\n"
            f"{{\n"
            f'  "crop_name": "{crop_name}",\n'
            f'  "sowing_date": "{sowing_date_str}",\n'
            f'  "acreage": {acreage},\n'
            f'  "stages": [\n'
            f'    {{"stage_number": "01", "stage_name": "बुवाई व अंकुरण (Sowing & Germination)", "days_from_sowing": 0, "target_date": "YYYY-MM-DD", "description": "..."}},\n'
            f'    {{"stage_number": "02", "stage_name": "...", "days_from_sowing": 21, "target_date": "YYYY-MM-DD", "description": "..."}}\n'
            f'  ],\n'
            f'  "irrigation_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "...", "description": "...", "priority": "high"}}\n'
            f'  ],\n'
            f'  "fertilizer_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "...", "dosage_kg": "...", "description": "...", "priority": "high"}}\n'
            f'  ],\n'
            f'  "pesticide_tasks": [\n'
            f'    {{"title": "...", "due_date": "YYYY-MM-DD", "stage": "...", "preventative_spray": "...", "dosage": "...", "description": "...", "priority": "normal"}}\n'
            f'  ]\n'
            f"}}"
        )

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
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
                parsed["ai_provider"] = "DeepSeek AI (deepseek-chat)"
                return parsed
            else:
                err_msg = f"HTTP {res.status_code}: {res.text[:200]}"
                logger.warning(f"[DeepSeek] API request failed: {err_msg}")
                raise RuntimeError(err_msg)
