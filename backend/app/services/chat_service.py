import uuid
import datetime
import json
from typing import Dict, Any, List
from app.database import execute_db, query_db, query_one
from app.services.privacy_firewall import PrivacyFirewall
from app.adapters.fallback import fallback_orchestrator
from app.utils.language import detect_language

class ChatService:
    @staticmethod
    async def ask_question(
        farmer_id: str = "farmer-1001",
        question: str = "",
        conversation_id: str = None,
        language: str = None,
        crop_context: str = None
    ) -> Dict[str, Any]:
        # 1. Privacy Firewall: Redact sensitive PII before processing
        clean_question = PrivacyFirewall.sanitize_prompt(question)
        
        # 2. Language Detection
        detected_lang = language or detect_language(clean_question)
        
        # 3. Process with AgriRAG Engine (Farmer Farm context + Weather + ICAR/TNAU/FAO Knowledge + Safety)
        from app.services.agri_rag import AgriRAGService
        rag_output = await AgriRAGService.process_agricultural_query(
            question=clean_question,
            farmer_id=farmer_id,
            language=detected_lang,
            crop_context=crop_context
        )
        
        ai_result = {
            "response": rag_output["response"],
            "provider": rag_output["provider"],
            "evidence_used": rag_output["evidence"]
        }
        
        # 5. Persist to SQLite
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
        now_str = datetime.datetime.utcnow().isoformat()
        
        existing_conv = query_one("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        if not existing_conv:
            execute_db("""
                INSERT INTO conversations (id, farmer_id, language, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (conv_id, farmer_id, detected_lang, now_str, now_str))
        else:
            execute_db("UPDATE conversations SET updated_at = ? WHERE id = ?", (now_str, conv_id))

        farmer_msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        ai_msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        evidence_json = json.dumps(ai_result.get("evidence_used", []))

        # Save farmer message
        execute_db("""
            INSERT INTO messages (id, conversation_id, sender, content, provider, evidence_json, created_at)
            VALUES (?, ?, 'farmer', ?, NULL, NULL, ?)
        """, (farmer_msg_id, conv_id, question, now_str))

        # Save AI verified message
        execute_db("""
            INSERT INTO messages (id, conversation_id, sender, content, provider, evidence_json, created_at)
            VALUES (?, ?, 'ai', ?, ?, ?, ?)
        """, (ai_msg_id, conv_id, ai_result["response"], ai_result["provider"], evidence_json, now_str))

        return {
            "conversation_id": conv_id,
            "response": ai_result["response"],
            "language": detected_lang,
            "provider": ai_result["provider"],
            "evidence": ai_result.get("evidence_used", []),
            "verified": ai_result.get("verified", True)
        }

    @staticmethod
    def get_messages(conversation_id: str) -> List[Dict[str, Any]]:
        rows = query_db("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        for r in rows:
            if r.get("evidence_json"):
                try:
                    r["evidence_sources"] = json.loads(r["evidence_json"])
                except Exception:
                    r["evidence_sources"] = []
        return rows
