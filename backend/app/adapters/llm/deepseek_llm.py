import os
import httpx
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.adapters.llm.base import BaseLLMAdapter
from app.config import settings

logger = logging.getLogger("agrigo.deepseek")

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

class DeepSeekLLMAdapter(BaseLLMAdapter):
    """
    DeepSeek Agricultural AI Intelligence Adapter (deepseek-chat)
    Specialized for answering farmer queries, pest/disease diagnosis recommendations,
    and conversational agronomic advisory following ICAR & TNAU standards.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY", "")

    async def generate_response(
        self,
        prompt: str,
        context: List[Dict[str, str]],
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Uses DeepSeek AI (deepseek-chat) to answer farmer questions with verified agronomic evidence.
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not configured")

        evidence_text = "\n".join([f"- {c.get('title', 'Evidence')}: {c.get('content', '')}" for c in context]) if context else "General ICAR agronomical standards."
        lang_name = "Hindi (हिंदी)" if language == "hi" else ("English" if language == "en" else language)

        system_instruction = (
            f"You are AgriGo Farmer AI (किसान मित्र AI), an elite Indian Agricultural Scientist and Agronomist. "
            f"Always reply in {lang_name}. Use respectful, warm, and highly practical language (address the farmer as 'किसान भाई' or 'आप').\n"
            f"Mandatory Guidelines:\n"
            f"1. Directly answer the farmer's question with actionable, scientific agronomic solutions (ICAR, TNAU, and FAO standards).\n"
            f"2. Provide concrete numbers: exact fertilizer doses (Urea, DAP, MOP, micronutrients per acre or per pump) or seed rates.\n"
            f"3. Prioritize Integrated Pest Management (IPM), biological remedies (Neem oil 1500 PPM, Trichoderma, pheromone traps) before chemical pesticides.\n"
            f"4. If recommending chemicals, provide exact CIBRC/ICAR approved safe dosages (ml/L or g/L) and safety withholding intervals.\n"
            f"5. Keep the advice structured, crisp (bullet points), and easy to read on mobile."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "system", "content": f"Verified Agricultural Context & Local Weather:\n{evidence_text}"},
            {"role": "user", "content": prompt}
        ]

        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 800
                }
            )

            if res.status_code == 200:
                raw_data = res.json()
                content = raw_data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "provider": "DeepSeek AI (deepseek-chat)",
                    "model": "deepseek-chat",
                    "evidence_used": [c.get("title", "ICAR Guidelines") for c in context] if context else ["ICAR / TNAU / FAO Agricultural Knowledge Base"]
                }
            else:
                err_msg = f"HTTP {res.status_code}: {res.text[:200]}"
                logger.warning(f"[DeepSeek Farmer AI] API request failed: {err_msg}")
                raise RuntimeError(err_msg)

    async def generate_crop_schedule(
        self,
        crop_name: str,
        sowing_date_str: str,
        acreage: float,
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Legacy fallback crop schedule generator using DeepSeek Chat API.
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
            f"phenological stages (01 to 05), irrigation timing, acreage-scaled fertilizer doses (DAP, Urea, MOP in kg), "
            f"and preventative IPM pesticide / fungicide sprays in Hindi."
        )

        async with httpx.AsyncClient(timeout=35.0) as client:
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
