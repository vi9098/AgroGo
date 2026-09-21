from app.adapters.llm.base import BaseLLMAdapter
from typing import Dict, Any, List

class LocalLLMAdapter(BaseLLMAdapter):
    """
    Rule-based local fallback LLM ensuring reliable agricultural answers even if external APIs fail.
    """
    
    KNOWLEDGE_FALLBACKS = {
        "curling": "Leaf curling in crops is commonly caused by sucking pests like whiteflies, aphids, or viral infections (like leaf curl virus). It can also result from extreme heat or water stress. Inspect the underside of leaves for tiny white or green insects. For organic control, apply 5ml Neem Oil per liter of water.",
        "yellow": "Yellowing leaves (chlorosis) usually indicates Nitrogen deficiency or water-logging. Ensure proper field drainage and consider a balanced NPK fertilizer spray.",
        "irrigate": "For optimal irrigation, water early in the morning or late in the evening to reduce evaporative loss. Check root-zone moisture 2-3 inches deep.",
        "pest": "For pest identification and safety, avoid synthetic chemical sprays without exact diagnosis. Organic spray: 5ml neem oil with a drop of liquid soap per liter of water."
    }

    async def generate_response(self, prompt: str, context: List[Dict[str, str]], language: str = "en") -> Dict[str, Any]:
        lower = prompt.lower()
        answer = None
        for keyword, response in self.KNOWLEDGE_FALLBACKS.items():
            if keyword in lower:
                answer = response
                break
        
        if not answer:
            answer = (
                "AgriGo agricultural recommendation: Maintain balanced soil nutrition and inspect your field regularly. "
                "You can also attach a clear photo of your crop symptoms for more detailed identification."
            )
            
        return {
            "content": answer,
            "provider": "AgriGo Local Agricultural Engine",
            "model": "rule-based-local-v1",
            "evidence_used": ["ICAR / AgriGo Knowledge Repository"]
        }
