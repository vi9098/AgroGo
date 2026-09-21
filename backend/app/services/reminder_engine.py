"""
Smart Adaptive Farm Reminder Engine
Generates phenology-driven, weather-aware farming reminders and parses natural language requests.
Safety Rule: Never prescribe pesticides solely on calendar dates.
"""
import uuid
import datetime
import re
import logging
from typing import List, Dict, Any, Optional
from app.database import query_db, query_one, execute_db
from app.adapters.weather import WeatherProviderAdapter
from app.services.agri_knowledge import AGROVOC_CROPS, AgriKnowledgeService

logger = logging.getLogger("agrigo.reminder_engine")

class ReminderEngine:
    """Intelligent scheduling engine for adaptive agricultural tasks."""

    @classmethod
    async def generate_crop_timeline_reminders(cls, farmer_id: str, crop_name: str,
                                              sowing_date_str: str,
                                              field_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generates stage-based adaptive reminders based on crop phenology and current weather."""
        weather = await WeatherProviderAdapter.get_agricultural_weather()
        rain_soon = weather.get("rain_expected_24h", False)

        stage_info = AgriKnowledgeService.estimate_crop_stage(sowing_date_str, crop_name)
        age_days = stage_info["age_days"]
        crop_clean = crop_name.lower()

        now = datetime.datetime.utcnow()
        created_reminders = []

        # 1. Weather-aware Irrigation Check
        irr_title = f"{crop_name}: सिंचाई जांच (Irrigation Check)"
        if rain_soon:
            irr_desc = f"अगले 24-48 घंटों में बारिश की संभावना है ({weather.get('rain_prob_today_pct')}%). अभी पानी न दें, बारिश के बाद खेत में नमी देखकर निर्णय लें।"
            due_date = (now + datetime.timedelta(days=2)).strftime("दिन बाद (बारिश के बाद)")
        else:
            if stage_info["is_critical_water"]:
                irr_desc = f"फसल क्रांतिक अवस्था '{stage_info['stage_hi']}' पर है। यदि मिट्टी में नमी कम है, तो हल्की सिंचाई करें।"
                due_date = "कल सुबह (06:00 AM)"
            else:
                irr_desc = "मिट्टी की ऊपरी 2-3 इंच सतह की नमी जांचें।"
                due_date = "2 दिन बाद"

        created_reminders.append({
            "title": irr_title,
            "description": irr_desc,
            "due_date": due_date,
            "type": "irrigation",
            "priority": "high" if stage_info["is_critical_water"] else "normal"
        })

        # 2. Field Pest/Disease Inspection (Monitoring only - NO unverified chemical prescription!)
        inspect_title = f"{crop_name}: कीट व रोग निरीक्षण (Field Scouting)"
        if "tomato" in crop_clean:
            inspect_desc = "पत्तियों के निचले हिस्से में सफेद मक्खी (Whitefly) या मरोड़िया लक्षण देखें। पीले चिपचिपे कार्ड जांचें। (रासायनिक कीटनाशक केवल कीट दिखने पर ही डालें)"
        elif "wheat" in crop_clean:
            inspect_desc = "पत्तियों पर पीले रतुआ (Yellow Rust) के धब्बे या दीमक की जांच करें।"
        else:
            inspect_desc = "फसल में नए कल्ले व पत्तों की स्थिति का निरीक्षण करें।"

        created_reminders.append({
            "title": inspect_title,
            "description": inspect_desc,
            "due_date": "3 दिन बाद",
            "type": "inspection",
            "priority": "normal"
        })

        # 3. Nutrient / Weed Monitoring
        if age_days <= 30:
            nut_title = f"{crop_name}: खरपतवार व पोषण जांच (Weeding & Nutrients)"
            nut_desc = "शुरुआती बढ़वार में खरपतवार प्रतिस्पर्धा रोकें। आवश्यकतानुसार हल्की निराई-गुड़ाई करें।"
            created_reminders.append({
                "title": nut_title,
                "description": nut_desc,
                "due_date": "अगले सप्ताह",
                "type": "nutrient",
                "priority": "normal"
            })

        # Persist reminders in SQLite
        for rem in created_reminders:
            rem_id = f"rem-{uuid.uuid4().hex[:8]}"
            execute_db("""
                INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, priority, created_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
            """, (rem_id, farmer_id, rem["title"], rem["description"], rem["due_date"], rem["type"], rem["priority"], now.isoformat()))
            rem["id"] = rem_id

        return created_reminders

    @classmethod
    def parse_natural_language_reminder(cls, text: str, farmer_id: str) -> Optional[Dict[str, Any]]:
        """Parses natural language requests like 'Remind me to check wheat every Sunday'."""
        text_clean = text.lower()
        now = datetime.datetime.utcnow()

        # Check intent
        reminder_keywords = ["remind", "याद दिलाना", "रिमाइंडर", "स्मरण", "चेक", "पानी"]
        if not any(kw in text_clean for kw in reminder_keywords):
            return None

        # Extract Crop
        crop = "फसल"
        for c in ["wheat", "गेहूं", "tomato", "टमाटर", "rice", "धान", "mustard", "सरसों"]:
            if c in text_clean:
                crop = c.capitalize()
                break

        # Extract Time/Date
        due_date = "कल शाम"
        if "sunday" in text_clean or "रविवार" in text_clean:
            due_date = "हर रविवार (Every Sunday)"
        elif "tomorrow" in text_clean or "कल" in text_clean:
            due_date = "कल शाम 05:00 PM"
        elif "next week" in text_clean or "अगले सप्ताह" in text_clean:
            due_date = "अगले सप्ताह"

        title = f"{crop} कृषि कार्य अनुस्मारक"
        description = f"किसान अनुरोध अनुसार: {text}"
        rem_id = f"rem-{uuid.uuid4().hex[:8]}"

        execute_db("""
            INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, priority, created_at)
            VALUES (?, ?, ?, ?, ?, 0, 'natural_language', 'high', ?)
        """, (rem_id, farmer_id, title, description, due_date, now.isoformat()))

        return {
            "id": rem_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "status": "created"
        }
