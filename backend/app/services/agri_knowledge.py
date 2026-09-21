"""
AgriGo Agricultural Knowledge Engine with AGROVOC Terminology Mapping
Integrates ICAR, TNAU, and FAO knowledge with multilingual concept graphs.
"""
import logging
from typing import List, Dict, Any, Optional
from app.database import query_db, query_one, execute_db

logger = logging.getLogger("agrigo.knowledge")

# Multilingual AGROVOC Agricultural Concept Graph
AGROVOC_CROPS = {
    "wheat": {
        "scientific_name": "Triticum aestivum",
        "standard_en": "Wheat",
        "standard_hi": "गेहूं",
        "synonyms": ["गेहूं", "gehu", "wheat", "gehoon", "kanak", "godhumai", "godhuma"],
        "critical_stages": [
            {"stage": "Germination", "day_start": 1, "day_end": 7, "hi": "अंकुरण"},
            {"stage": "Crown Root Initiation (CRI)", "day_start": 20, "day_end": 25, "hi": "शीर्ष जड़ विकास (CRI)", "critical_water": True},
            {"stage": "Tillering", "day_start": 40, "day_end": 45, "hi": "कल्ले फूटना"},
            {"stage": "Jointing", "day_start": 60, "day_end": 65, "hi": "गांठ बनना", "critical_water": True},
            {"stage": "Flowering / Heading", "day_start": 80, "day_end": 85, "hi": "फूल आना / बाली निकलना", "critical_water": True},
            {"stage": "Milking / Grain Filling", "day_start": 100, "day_end": 105, "hi": "दुग्ध अवस्था"},
            {"stage": "Maturity & Harvest", "day_start": 120, "day_end": 135, "hi": "परिपक्वता व कटाई"}
        ]
    },
    "tomato": {
        "scientific_name": "Solanum lycopersicum",
        "standard_en": "Tomato",
        "standard_hi": "टमाटर",
        "synonyms": ["टमाटर", "tamatar", "tomato", "thakkali"],
        "critical_stages": [
            {"stage": "Nursery & Transplanting", "day_start": 1, "day_end": 25, "hi": "नर्सरी व रोपाई"},
            {"stage": "Vegetative Establishment", "day_start": 26, "day_end": 45, "hi": "वानस्पतिक वृद्धि"},
            {"stage": "Flowering & Fruit Set", "day_start": 46, "day_end": 70, "hi": "फूल व फल लगना", "critical_water": True},
            {"stage": "Fruit Development & Picking", "day_start": 71, "day_end": 120, "hi": "फल विकास व तुड़ाई"}
        ]
    },
    "rice": {
        "scientific_name": "Oryza sativa",
        "standard_en": "Rice / Paddy",
        "standard_hi": "धान / चावल",
        "synonyms": ["धान", "चावल", "rice", "paddy", "dhan", "chawal", "nellu"],
        "critical_stages": [
            {"stage": "Transplanting", "day_start": 1, "day_end": 10, "hi": "रोपाई"},
            {"stage": "Active Tillering", "day_start": 20, "day_end": 35, "hi": "कल्ले निकलना", "critical_water": True},
            {"stage": "Panicle Initiation", "day_start": 50, "day_end": 65, "hi": "बाली का बनना", "critical_water": True},
            {"stage": "Flowering", "day_start": 70, "day_end": 80, "hi": "फूल अवस्था", "critical_water": True},
            {"stage": "Maturity", "day_start": 100, "day_end": 125, "hi": "कटाई"}
        ]
    },
    "mustard": {
        "scientific_name": "Brassica juncea",
        "standard_en": "Mustard",
        "standard_hi": "सरसों / राई",
        "synonyms": ["सरसों", "sarson", "mustard", "rai", "toria", "kadugu"],
        "critical_stages": [
            {"stage": "Vegetative", "day_start": 1, "day_end": 30, "hi": "वानस्पतिक वृद्धि"},
            {"stage": "Flowering", "day_start": 35, "day_end": 50, "hi": "फूल आना", "critical_water": True},
            {"stage": "Pod Filling", "day_start": 60, "day_end": 85, "hi": "फली भरना", "critical_water": True},
            {"stage": "Maturity", "day_start": 100, "day_end": 120, "hi": "परिपक्वता"}
        ]
    }
}

AGROVOC_PROBLEMS = {
    "leaf_curl": {
        "concept": "Tomato Leaf Curl Begomovirus (ToLCV)",
        "vector": "Whitefly (Bemisia tabaci) / सफेद मक्खी",
        "synonyms": ["पत्ते मुड़ रहे", "पत्ती मरोड़", "पत्ता मरोड़", "मुड़ रहे", "मुड़", "मरोड़", "मरोड़िया", "leaf curl", "curling", "murda", "mattha", "churda"],
        "crops": ["tomato", "cotton", "chilli", "papaya"],
        "immediate_action": "पीले चिपचिपे कार्ड (Yellow Sticky Traps - 15 प्रति एकड़) लगाएं। नीम का तेल (Neem Oil 5ml/L पानी) का छिड़काव पत्तियों के निचले हिस्से पर करें।",
        "chemical_intervention": "सफेद मक्खी अत्यधिक होने पर कृषि विशेषज्ञ की सलाह से इमिडाक्लोप्रिड 17.8 SL @ 0.5 मिली प्रति लीटर पानी का छिड़काव करें। प्रतीक्षा अवधि (Waiting period): 3 दिन।",
        "source": "ICAR - Indian Institute of Horticultural Research"
    },
    "yellow_rust": {
        "concept": "Yellow / Stripe Rust (Puccinia striiformis)",
        "synonyms": ["पीला रोग", "हल्दी रोग", "yellow rust", "stripe rust", "peela rog", "haldiya"],
        "crops": ["wheat"],
        "immediate_action": "पत्तियों पर पीले रंग की धारियां या पाउडर जैसी रचना दिखती है। संक्रमित पत्तियों को तुरंत हटाएं व नाइट्रोजन का अधिक प्रयोग रोकें।",
        "chemical_intervention": "रोग के शुरुआती लक्षण दिखने पर प्रोपिकोनाजोल 25 EC (Tilt) @ 1 मिली प्रति लीटर पानी में मिलाकर साफ मौसम में छिड़काव करें।",
        "source": "ICAR - Indian Agricultural Research Institute (IARI)"
    },
    "blast": {
        "concept": "Rice / Paddy Blast (Magnaporthe oryzae)",
        "synonyms": ["ब्लास्ट", "झुलसा", "blast", "dhan blast", "jhulsa", "khaira"],
        "crops": ["rice"],
        "immediate_action": "स्यूडोमोनास फ्लोरोसेंस (Pseudomonas fluorescens) 5 ग्राम प्रति लीटर पानी का छिड़काव करें। खेत में अत्यधिक यूरिया देने से बचें।",
        "chemical_intervention": "उग्र प्रकोप पर ट्राइसाइक्लाजोल 75 WP (Beam) @ 0.6 ग्राम प्रति लीटर पानी का छिड़काव करें।",
        "source": "TNAU Agritech Portal & ICAR - National Rice Research Institute"
    },
    "aphid": {
        "concept": "Mustard Aphid (Lipaphis erysimi) / चेपा - माहू",
        "synonyms": ["माहू", "चेपा", "aphid", "mahu", "chepa", "mowla"],
        "crops": ["mustard"],
        "immediate_action": "शुरुआती अवस्था में जैविक नियंत्रण: 2% नीम तेल या वर्टिसिलियम लेकानी (Verticillium lecanii) 5 ग्राम/लीटर का छिड़काव।",
        "chemical_intervention": "आर्थिक क्षति स्तर (25 माहू प्रति टहनी) पार होने पर डाइमेथोएट 30 EC @ 1 मिली प्रति लीटर। प्रतीक्षा अवधि: 10 दिन।",
        "source": "ICAR - Directorate of Rapeseed-Mustard Research"
    }
}

class AgriKnowledgeService:
    """Service to bridge farmer queries with AGROVOC terminology and trusted evidence."""

    @staticmethod
    def resolve_agrovoc_concept(text: str) -> Dict[str, Any]:
        """Maps user question text to standard crop and disease concepts."""
        text_lower = text.lower()
        matched_crop = None
        matched_problem = None

        # 1. Match Crop
        for crop_key, crop_info in AGROVOC_CROPS.items():
            for syn in crop_info["synonyms"]:
                if syn.lower() in text_lower:
                    matched_crop = crop_key
                    break
            if matched_crop:
                break

        # 2. Match Problem
        for prob_key, prob_info in AGROVOC_PROBLEMS.items():
            for syn in prob_info["synonyms"]:
                if syn.lower() in text_lower:
                    matched_problem = prob_info
                    break
            if matched_problem:
                break

        return {
            "matched_crop": matched_crop,
            "crop_meta": AGROVOC_CROPS.get(matched_crop) if matched_crop else None,
            "matched_problem": matched_problem
        }

    @staticmethod
    def retrieve_evidence(crop: Optional[str], topic: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieves authoritative knowledge chunks from ICAR, TNAU, and FAO."""
        if crop:
            sql = "SELECT * FROM knowledge_chunks WHERE LOWER(crop) = LOWER(?) ORDER BY confidence DESC LIMIT ?"
            params = (crop, limit)
        else:
            sql = "SELECT * FROM knowledge_chunks ORDER BY confidence DESC LIMIT ?"
            params = (limit,)
        
        chunks = query_db(sql, params)
        return chunks

    @staticmethod
    def estimate_crop_stage(sowing_date_str: str, crop_name: str) -> Dict[str, Any]:
        """Calculates current growth stage, age in days, and critical care guidelines."""
        import datetime
        try:
            sowing_dt = datetime.datetime.strptime(sowing_date_str, "%Y-%m-%d")
            today = datetime.datetime.utcnow()
            age_days = max(1, (today - sowing_dt).days)
        except Exception:
            age_days = 20

        crop_key = crop_name.lower()
        crop_data = AGROVOC_CROPS.get(crop_key, AGROVOC_CROPS.get("wheat"))
        current_stage = "Vegetative Growth"
        stage_hi = "वानस्पतिक वृद्धि"
        is_critical_water = False

        if crop_data:
            for st in crop_data["critical_stages"]:
                if st["day_start"] <= age_days <= st["day_end"]:
                    current_stage = st["stage"]
                    stage_hi = st.get("hi", current_stage)
                    is_critical_water = st.get("critical_water", False)
                    break
            else:
                if age_days > 120:
                    current_stage = "Maturity / Harvesting"
                    stage_hi = "परिपक्वता व कटाई"

        return {
            "crop": crop_name,
            "age_days": age_days,
            "current_stage": current_stage,
            "stage_hi": stage_hi,
            "is_critical_water": is_critical_water
        }

    @staticmethod
    def list_knowledge_sources() -> List[Dict[str, Any]]:
        """Returns registered sources with robots and licensing metadata."""
        return query_db("SELECT * FROM knowledge_sources ORDER BY name ASC")

    @staticmethod
    def record_farmer_observation(farmer_id: str, crop: str, location: str,
                                   problem: str, pest: str = None,
                                   treatment: str = None, result: str = None) -> str:
        """Stores a farmer observation as COMMUNITY_OBSERVATION for candidate review."""
        import uuid, datetime
        obs_id = f"obs-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.utcnow().isoformat()
        execute_db("""
            INSERT INTO farmer_observations (id, farmer_id, crop, location, problem, observed_pest, treatment_applied, result, evidence_type, validation_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'COMMUNITY_OBSERVATION', 'pending_review', ?)
        """, (obs_id, farmer_id, crop, location, problem, pest, treatment, result, now))
        return obs_id
