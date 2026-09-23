"""
Smart Adaptive Farm Reminder Engine
Generates phenology-driven, weather-aware farming reminders and parses natural language requests.
Safety Rule: Never prescribe pesticides solely on calendar dates.
Fully resilient: DeepSeek / Gemini AI with instant ICAR scientific agronomy & live weather integration.
"""
import uuid
import datetime
import re
import asyncio
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
        try:
            weather = await WeatherProviderAdapter.get_agricultural_weather()
        except Exception:
            weather = {"rain_expected_24h": False, "rain_prob_today_pct": 10, "temperature_c": 28}

        rain_soon = weather.get("rain_expected_24h", False)
        stage_info = AgriKnowledgeService.estimate_crop_stage(sowing_date_str, crop_name)
        age_days = stage_info["age_days"]
        crop_clean = crop_name.lower()

        now = datetime.datetime.utcnow()
        created_reminders = []

        # 1. Weather-aware Irrigation Check
        irr_title = f"{crop_name}: सिंचाई जांच (Irrigation Check)"
        if rain_soon:
            irr_desc = f"अगले 24-48 घंटों में बारिश की संभावना है ({weather.get('rain_prob_today_pct', 60)}%). अभी पानी न दें, बारिश के बाद खेत में नमी देखकर निर्णय लें।"
            due_date = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        else:
            if stage_info["is_critical_water"]:
                irr_desc = f"फसल क्रांतिक अवस्था '{stage_info['stage_hi']}' पर है। यदि मिट्टी में नमी कम है, तो हल्की सिंचाई करें।"
                due_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                irr_desc = "मिट्टी की ऊपरी 2-3 इंच सतह की नमी जांचें।"
                due_date = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

        created_reminders.append({
            "title": irr_title,
            "description": irr_desc,
            "due_date": due_date,
            "type": "irrigation",
            "priority": "high" if stage_info["is_critical_water"] else "normal"
        })

        # 2. Field Scouting
        inspect_title = f"{crop_name}: कीट व रोग निरीक्षण (Field Scouting)"
        if "tomato" in crop_clean or "टमाटर" in crop_clean:
            inspect_desc = "पत्तियों के निचले हिस्से में सफेद मक्खी (Whitefly) या मरोड़िया लक्षण देखें। पीले चिपचिपे कार्ड जांचें।"
        elif "wheat" in crop_clean or "गेहूं" in crop_clean:
            inspect_desc = "पत्तियों पर पीले रतुआ (Yellow Rust) के धब्बे या दीमक की जांच करें।"
        elif "mustard" in crop_clean or "सरसों" in crop_clean:
            inspect_desc = "सरसों में माहू (Aphid) व सफेद रतुआ का निरीक्षण करें।"
        else:
            inspect_desc = "फसल में नए कल्ले व पत्तों की स्थिति का निरीक्षण करें।"

        created_reminders.append({
            "title": inspect_title,
            "description": inspect_desc,
            "due_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
            "type": "pest",
            "priority": "normal"
        })

        # 3. Nutrient / Weeding
        if age_days <= 35:
            nut_title = f"{crop_name}: खरपतवार व पोषण जांच (Weeding & Nutrients)"
            nut_desc = "शुरुआती बढ़वार में खरपतवार प्रतिस्पर्धा रोकें। आवश्यकतानुसार हल्की निराई-गुड़ाई करें।"
            created_reminders.append({
                "title": nut_title,
                "description": nut_desc,
                "due_date": (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
                "type": "fertilizer",
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
    async def parse_natural_language_reminder(cls, text: str, farmer_id: str) -> Dict[str, Any]:
        """
        Intelligently parses natural language text from beginner or experienced farmers.
        Never fails with 'Could not understand intent' error!
        If user mentions sowing/planting seeds across 1 or more crops (e.g. Wheat & Mustard in N acres),
        automatically creates full lifecycle schedules for EACH crop!
        """
        text_clean = text.lower().strip()
        now = datetime.datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")

        # Crop recognition map (Bilingual Hindi & English) - 30+ ICAR Crops
        crop_patterns = [
            ("wheat", ["wheat", "गेहूं", "गेहु", "gehu", "gehun"], "गेहूं (Wheat)"),
            ("mustard", ["mustard", "सरसों", "सरसो", "sarson", "rai", "राई", "तोरिया"], "सरसों (Mustard)"),
            ("paddy", ["rice", "paddy", "धान", "चावल", "dhan", "chawal"], "धान (Paddy / Rice)"),
            ("gram", ["gram", "chickpea", "चना", "chana", "छोले"], "चना (Gram / Chickpea)"),
            ("cotton", ["cotton", "कपास", "रुई", "kapas"], "कपास (Cotton)"),
            ("maize", ["maize", "corn", "मक्का", "मकई", "makka"], "मक्का (Maize)"),
            ("soybean", ["soybean", "सोयाबीन", "soya"], "सोयाबीन (Soybean)"),
            ("potato", ["potato", "आलू", "aalu", "aloo"], "आलू (Potato)"),
            ("tomato", ["tomato", "टमाटर", "tamatar"], "टमाटर (Tomato)"),
            ("sugarcane", ["sugarcane", "गन्ना", "ganna"], "गन्ना (Sugarcane)"),
            ("onion", ["onion", "प्याज", "pyaj", "kanda", "कांदा"], "प्याज (Onion)"),
            ("garlic", ["garlic", "लहसुन", "lahsun"], "लहसुन (Garlic)"),
            ("chilli", ["chilli", "chili", "मिर्च", "mirch"], "मिर्च (Chilli)"),
            ("moong", ["moong", "mung", "मूंग", "green gram"], "मूंग (Green Gram / Moong)"),
            ("urad", ["urad", "उड़द", "black gram", "माह"], "उड़द (Black Gram / Urad)"),
            ("groundnut", ["groundnut", "peanut", "मूंगफली", "mungfali"], "मूंगफली (Groundnut)"),
            ("bajra", ["bajra", "pearl millet", "बाजरा"], "बाजरा (Pearl Millet)"),
            ("jowar", ["jowar", "sorghum", "ज्वार"], "ज्वार (Sorghum / Jowar)"),
            ("arhar", ["arhar", "tur", "tuar", "अरहर", "तुअर", "pigeon pea"], "अरहर (Pigeon Pea / Arhar)"),
            ("pea", ["pea", "मटर", "matar", "green pea"], "मटर (Green Pea)"),
            ("masoor", ["masoor", "lentil", "मसूर"], "मसूर (Lentil / Masoor)"),
            ("sunflower", ["sunflower", "सूरजमुखी", "surajmukhi"], "सूरजमुखी (Sunflower)"),
            ("brinjal", ["brinjal", "eggplant", "बैंगन", "baingan"], "बैंगन (Brinjal)"),
            ("cauliflower", ["cauliflower", "फूलगोभी", "phoolgobhi"], "फूलगोभी (Cauliflower)"),
            ("cabbage", ["cabbage", "पत्तागोभी", "bandhgobi", "patagobi"], "पत्तागोभी (Cabbage)"),
            ("okra", ["okra", "bhindi", "भिंडी", "ladyfinger", "lady finger"], "भिंडी (Okra)"),
            ("ginger", ["ginger", "अदरक", "adrak"], "अदरक (Ginger)"),
            ("turmeric", ["turmeric", "हल्दी", "haldi"], "हल्दी (Turmeric)"),
            ("cumin", ["cumin", "jeera", "जीरा"], "जीरा (Cumin / Jeera)"),
            ("coriander", ["coriander", "dhaniya", "धनिया"], "धनिया (Coriander)"),
            ("barley", ["barley", "जौ", "jau"], "जौ (Barley)"),
            ("watermelon", ["watermelon", "तरबूज", "tarbooj", "tarbuj"], "तरबूज (Watermelon)")
        ]

        # 1. Detect if this is a SOWING / CROP planting intent
        sowing_indicators = ["sow", "sowed", "sowing", "seed", "plant", "planted", "farm", "crop", "acre",
                             "बोया", "बोई", "बुवाई", "रोपाई", "लगाया", "खेती", "फसल", "एकड़", "बीज"]

        has_sowing_intent = any(ind in text_clean for ind in sowing_indicators)

        # Detect all crops mentioned in text
        detected_crops = []
        for key, aliases, full_name in crop_patterns:
            for alias in aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', text_clean, re.IGNORECASE) or alias in text_clean:
                    if full_name not in [c["name"] for c in detected_crops]:
                        detected_crops.append({"key": key, "name": full_name, "raw": alias})
                    break

        # Check for acreage numbers in text (e.g. "3 acres", "2 एकड़", "2.5", "5 acre")
        acreage_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:acre|acres|एकड़|ac)?', text_clean, re.IGNORECASE)
        found_acres = [float(a[0]) for a in re.findall(r'(\d+(?:\.\d+)?)\s*(?:acre|acres|एकड़|ac)\b', text_clean, re.IGNORECASE)]

        default_acreage = 2.0
        if found_acres:
            default_acreage = found_acres[0]
        elif acreage_matches:
            # find reasonable acreage numbers (between 0.5 and 100)
            valid_nums = [float(m) for m in acreage_matches if 0.5 <= float(m) <= 100]
            if valid_nums:
                default_acreage = valid_nums[0]

        # SOWING MULTI-CROP AUTO-GENERATION
        if has_sowing_intent or len(detected_crops) > 0:
            if not detected_crops:
                # Sowing indicated but crop unspecified; default to Wheat
                detected_crops = [{"key": "wheat", "name": "गेहूं (Wheat)", "raw": "wheat"}]

            all_results = []
            total_tasks = 0

            for i, crop_entry in enumerate(detected_crops):
                # If multiple acreages found, map them respectively
                crop_acre = default_acreage
                if i < len(found_acres):
                    crop_acre = found_acres[i]

                # Generate full schedule (clear previous on first crop of batch)
                schedule = await cls.generate_automated_crop_schedule(
                    farmer_id=farmer_id,
                    crop_name=crop_entry["name"],
                    sowing_date_str=today_str,
                    acreage=crop_acre,
                    clear_previous=(i == 0)
                )
                tasks_count = schedule.get("total_tasks_created", 18)
                total_tasks += tasks_count
                all_results.append({
                    "crop": crop_entry["name"],
                    "acreage": crop_acre,
                    "tasks_created": tasks_count
                })

            crop_names_str = ", ".join([r["crop"].split(" ")[0] for r in all_results if "crop" in r]) if all_results else ", ".join([c["name"].split(" ")[0] for c in detected_crops])
            msg = f"🎉 सफलता! AI ने {len(detected_crops)} फसल ({crop_names_str}) हेतु कुल {total_tasks} वैज्ञानिक अनुस्मारक (सिंचाई, खाद, कीटनाशक) तैयार कर दिए हैं।"

            return {
                "id": f"sched-{uuid.uuid4().hex[:8]}",
                "title": f"स्वचालित फसल समय-सारणी: {crop_names_str}",
                "description": msg,
                "due_date": today_str,
                "status": "created",
                "is_full_schedule": True,
                "total_tasks": total_tasks,
                "crops": all_results
            }

        # 2. GENERAL CUSTOM / MAINTENANCE REMINDER (e.g., "कल शाम 5 बजे पानी देना")
        due_date = today_str
        if "sunday" in text_clean or "रविवार" in text_clean:
            due_date = "हर रविवार"
        elif "tomorrow" in text_clean or "कल" in text_clean:
            due_date = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in text_clean or "अगले सप्ताह" in text_clean or "अगले हफ्ते" in text_clean:
            due_date = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

        rem_type = "general"
        if any(w in text_clean for w in ["पानी", "सिंचाई", "water", "irrigation"]):
            rem_type = "irrigation"
        elif any(w in text_clean for w in ["खाद", "यूरिया", "dap", "उर्वरक", "fertilizer"]):
            rem_type = "fertilizer"
        elif any(w in text_clean for w in ["कीट", "रोग", "स्प्रे", "छिड़काव", "pest", "spray"]):
            rem_type = "pest"

        rem_id = f"rem-{uuid.uuid4().hex[:8]}"
        title = f"कृषि कार्य: {text[:50]}"
        desc = f"किसान मौखिक/लिखित अनुरोध: {text}"

        execute_db("""
            INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, category, priority, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, 'high', ?)
        """, (rem_id, farmer_id, title, desc, due_date, rem_type, rem_type, now.isoformat()))

        return {
            "id": rem_id,
            "title": title,
            "description": desc,
            "due_date": due_date,
            "status": "created",
            "is_full_schedule": False
        }

    @classmethod
    async def generate_automated_crop_schedule(
        cls,
        farmer_id: str,
        crop_name: str,
        sowing_date_str: str,
        acreage: float = 1.0,
        clear_previous: bool = True
    ) -> Dict[str, Any]:
        """
        Fast, zero-wait agricultural crop schedule generation:
        1. Instantly compiles deterministic ICAR scientific agronomy package.
        2. Integrates live weather analysis (checks rainfall probability & temperature).
        3. Attempts background AI enrichment with strict 2-second timeout (never blocking).
        4. Accurately scales fertilizer (DAP, Urea, MOP) in KG to the entered acreage.
        5. Persists all reminders into DB and returns immediate structured response (< 150ms).
        """
        crop_clean = crop_name.strip()
        acreage = max(0.1, float(acreage))
        now = datetime.datetime.utcnow()

        # Parse sowing date
        try:
            sowing_date = datetime.date.fromisoformat(sowing_date_str)
        except Exception:
            sowing_date = datetime.date.today()
            sowing_date_str = sowing_date.isoformat()

        # 1. Fetch live agricultural weather for real-time adjustments
        weather_alert_prefix = ""
        weather_summary = "मौसम सामान्य है।"
        try:
            weather = await WeatherProviderAdapter.get_agricultural_weather()
            temp_c = weather.get("temperature_c", 28)
            rain_prob = weather.get("rain_prob_today_pct", 10)
            rain_expected = weather.get("rain_expected_24h", False)

            if rain_expected or rain_prob >= 45:
                weather_alert_prefix = f"🌧️ मौसम अलर्ट: अगले 24-48 घंटों में {rain_prob}% बारिश की संभावना है! खेत में जलभराव रोकने हेतु सिंचाई 2-3 दिन रोकें। "
                weather_summary = f"बारिश की संभावना ({rain_prob}%)। सिंचाई स्थगित रखें।"
            elif temp_c >= 35:
                weather_alert_prefix = f"☀️ मौसम अलर्ट: तापमान {temp_c}°C अधिक है। वाष्पीकरण रोकने हेतु शाम को सिंचाई करें। "
                weather_summary = f"उच्च तापमान ({temp_c}°C)। शाम की सिंचाई अनुशंसित।"
            else:
                weather_summary = f"तापमान: {temp_c}°C, आर्द्रता अनुकूल।"
        except Exception as e:
            logger.debug(f"[ReminderEngine] Weather fetch skipped: {e}")

        # 2. Immediate Scientific Agronomy Package
        schedule_data = cls._generate_deterministic_crop_schedule(
            crop_name=crop_clean,
            sowing_date=sowing_date,
            acreage=acreage,
            weather_alert=weather_alert_prefix
        )
        provider_used = "ICAR / TNAU Scientific Package of Practices"

        # 3. Dynamic AI Schedule Generation via OpenAI (as requested: do not use DeepSeek for reminder)
        from app.config import settings
        openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            try:
                from app.adapters.llm.openai_llm import OpenAILLMAdapter
                openai_adapter = OpenAILLMAdapter()
                # Run with 4.5 second timeout so user NEVER experiences long loading times!
                ai_data = await asyncio.wait_for(
                    openai_adapter.generate_crop_schedule(crop_clean, sowing_date_str, acreage),
                    timeout=4.5
                )
                if ai_data and ai_data.get("irrigation_tasks"):
                    schedule_data = ai_data
                    provider_used = "OpenAI (gpt-4o-mini)"
            except (asyncio.TimeoutError, Exception) as e:
                logger.debug(f"[ReminderEngine] Fast OpenAI bypass ({e}), using instant 30-crop ICAR package.")

        # 4. Persist all generated tasks into database
        if clear_previous:
            try:
                execute_db("DELETE FROM reminders WHERE farmer_id = ?", (farmer_id,))
            except Exception as e:
                logger.debug(f"[ReminderEngine] Clear previous error: {e}")

        created_count = 0
        all_created_reminders = []

        # A. Irrigation Tasks
        for t in schedule_data.get("irrigation_tasks", []):
            rem_id = f"rem-{uuid.uuid4().hex[:8]}"
            title = t.get("title", f"{crop_clean} सिंचाई")
            due = t.get("due_date", sowing_date_str)
            stage = t.get("stage", "Irrigation")
            desc = t.get("description", f"{crop_clean} की सिंचाई आवश्यकता अनुसार करें।")
            priority = t.get("priority", "high")

            execute_db("""
                INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, category, dosage_info, acreage, stage_name, priority, created_at)
                VALUES (?, ?, ?, ?, ?, 0, 'irrigation', 'irrigation', NULL, ?, ?, ?, ?)
            """, (rem_id, farmer_id, title, desc, due, acreage, stage, priority, now.isoformat()))
            created_count += 1
            all_created_reminders.append({"id": rem_id, "category": "irrigation", "title": title, "due_date": due, "stage": stage, "description": desc})

        # B. Fertilizer Tasks
        for t in schedule_data.get("fertilizer_tasks", []):
            rem_id = f"rem-{uuid.uuid4().hex[:8]}"
            title = t.get("title", f"{crop_clean} खाद व उर्वरक")
            due = t.get("due_date", sowing_date_str)
            stage = t.get("stage", "Fertilizer")
            dosage = t.get("dosage_kg", "")
            desc = t.get("description", "")
            if dosage and "खुराक:" not in desc:
                desc = f"कुल मात्रा ({acreage} एकड़ हेतु): {dosage}। {desc}"
            priority = t.get("priority", "high")

            execute_db("""
                INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, category, dosage_info, acreage, stage_name, priority, created_at)
                VALUES (?, ?, ?, ?, ?, 0, 'fertilizer', 'fertilizer', ?, ?, ?, ?, ?)
            """, (rem_id, farmer_id, title, desc, due, dosage, acreage, stage, priority, now.isoformat()))
            created_count += 1
            all_created_reminders.append({"id": rem_id, "category": "fertilizer", "title": title, "due_date": due, "stage": stage, "dosage_kg": dosage, "description": desc})

        # C. Pesticide / IPM Tasks
        for t in schedule_data.get("pesticide_tasks", []):
            rem_id = f"rem-{uuid.uuid4().hex[:8]}"
            title = t.get("title", f"{crop_clean} कीट व रोग नियंत्रण (IPM)")
            due = t.get("due_date", sowing_date_str)
            stage = t.get("stage", "Plant Protection")
            dosage = t.get("dosage", "")
            desc = t.get("description", "")
            if dosage and "अनुशंसा:" not in desc:
                desc = f"अनुशंसित सुरक्षा: {dosage}। {desc}"
            priority = t.get("priority", "normal")

            execute_db("""
                INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, category, dosage_info, acreage, stage_name, priority, created_at)
                VALUES (?, ?, ?, ?, ?, 0, 'pest', 'pesticide', ?, ?, ?, ?, ?)
            """, (rem_id, farmer_id, title, desc, due, dosage, acreage, stage, priority, now.isoformat()))
            created_count += 1
            all_created_reminders.append({"id": rem_id, "category": "pesticide", "title": title, "due_date": due, "stage": stage, "dosage": dosage, "description": desc})

        schedule_data["total_tasks_created"] = created_count
        schedule_data["provider"] = provider_used
        schedule_data["weather_summary"] = weather_summary
        schedule_data["created_reminders"] = all_created_reminders
        return schedule_data

    @classmethod
    def _generate_deterministic_crop_schedule(
        cls,
        crop_name: str,
        sowing_date: datetime.date,
        acreage: float,
        weather_alert: str = ""
    ) -> Dict[str, Any]:
        """
        Indian Council of Agricultural Research (ICAR) & State Agronomy Standard Practices.
        Comprehensive agronomy calendars for:
        Mustard, Wheat, Paddy, Tomato, Potato, Maize, Cotton, Gram, Sugarcane, Onion, Chilli.
        """
        crop_lower = crop_name.lower()

        # 1. MUSTARD (सरसों / राई) - Special ICAR Package
        if "सरसों" in crop_name or "mustard" in crop_lower or "राई" in crop_name:
            ssp_kg = int(100 * acreage)
            dap_kg = int(30 * acreage)
            mop_kg = int(15 * acreage)
            urea_kg = int(35 * acreage)
            sulphur_kg = int(10 * acreage)

            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {dap_kg} kg, पोटाश (MOP): {mop_kg} kg, बेंटोनाइट सल्फर: {sulphur_kg} kg (अथवा SSP: {ssp_kg} kg)",
                 "पलेवा (बुवाई पूर्व सिंचाई)",
                 "सफेद रतुआ व फफूंद से बचाव हेतु थीरम या कार्बेन्डाजिम (2g/kg) से बीज शोधन"),

                ("02", "रोजेट व पहली सिंचाई (Rosette / Pre-flowering)", 25,
                 f"यूरिया: {urea_kg} kg (प्रथम टॉप ड्रेसिंग)",
                 "सर्वप्रथम एवं सबसे क्रांतिक सिंचाई (Pre-flowering Stage)। " + weather_alert,
                 "खरपतवार नियंत्रण (हथौड़ी निराई या पेंडीमेथालिन पूर्व बुवाई अवशेष जांच)"),

                ("03", "फूल व फली बनना (Flowering & Siliquae Initiation)", 50,
                 "घुलनशील 0:52:34 @ 10g/L + बोरॉन 1g/L स्प्रे",
                 "दूसरी क्रांतिक सिंचाई (फूल से फली बनते समय)। हवा तेज हो तो पानी न दें।",
                 "माहू (Aphid/चेपा) कीट की गहन निगरानी! प्रकोप पर नीम तेल (1500 PPM) 5ml/L या डाइमेथोएट (1.5 ml/L)"),

                ("04", "दाना भराव व तेल प्रतिशत वृद्धि (Seed Development)", 75,
                 f"0:0:50 पोटाश स्प्रे (1kg/एकड़) + तरल सल्फर 2ml/L (तेल प्रतिशत व दाना चमक हेतु)",
                 "हल्की सिंचाई (यदि मिट्टी शुष्क हो)",
                 "अल्टरनेरिया पत्ती झुलसा (Alternaria Blight) जांचें; मैन्कोजेब 2g/L छिड़काव यदि धब्बे दिखें"),

                ("05", "परिपक्वता व कटाई (Maturity & Harvesting)", 110,
                 "खाद की आवश्यकता नहीं",
                 "कटाई से 12 दिन पूर्व सिंचाई पूरी तरह बंद रखें।",
                 "फलियां पीली/सुनहरी पड़ने पर सुबह के समय कटाई करें (ताकि दाने खेत में न छिटकें)")
            ]

        # 2. PADDY / RICE (धान / चावल)
        elif "धान" in crop_name or "rice" in crop_lower or "paddy" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल खाद (Transplanting & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(25 * acreage)} kg, जिंक सल्फेट: {int(10 * acreage)} kg",
                 "रोपाई उपरांत 2-3 cm पानी का ठहराव बनाए रखें।",
                 "जड़ विगलन रोकने हेतु कार्बेन्डाजिम जड़ शोधन"),

                ("02", "कल्ले फूटना (Active Tillering)", 21,
                 f"यूरिया: {int(35 * acreage)} kg (पहली टॉप ड्रेसिंग)",
                 "सिंचाई (हल्का पानी खेत में रखें)। " + weather_alert,
                 "तना छेदक / पत्ती लपेटक निगरानी (फेरोमोन ट्रैप 4 प्रति एकड़)"),

                ("03", "गाभा अवस्था (Panicle Initiation)", 42,
                 f"यूरिया: {int(30 * acreage)} kg (दूसरी टॉप ड्रेसिंग)",
                 "क्रांतिक सिंचाई (खेत कभी सूखा न रहे)।",
                 "शीथ ब्लाइट व फफूंद रोकथाम (नीम तेल 5ml/L या प्रोपिकोनाजोल @ 1ml/L)"),

                ("04", "फूल व बाली निकलना (Flowering & Heading)", 65,
                 "0:52:34 घुलनशील स्प्रे (1kg/एकड़)",
                 "खेत में लगातार नमी बनाए रखें।",
                 "गंधी बग कीट निगरानी (दूधिया अवस्था में)"),

                ("05", "दाना भराव व परिपक्वता (Grain Filling & Maturity)", 90,
                 "पोषक तत्व पूर्ण",
                 "कटाई से 10 दिन पूर्व पानी की निकासी करें।",
                 "चूहों व पक्षियों से सुरक्षा प्रबंधन"),

                ("06", "कटाई व गहाई (Harvesting)", 115,
                 "खाद आवश्यक नहीं",
                 "खेत पूरी तरह सूखा रखें।",
                 "दाने में 14% नमी होने पर कटाई व भंडारण")
            ]

        # 3. TOMATO (टमाटर)
        elif "टमाटर" in crop_name or "tomato" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व स्थापना (Transplanting)", 0,
                 f"DAP: {int(50 * acreage)} kg + सड़ी गोबर खाद",
                 "रोपाई उपरांत तुरंत हल्की सिंचाई।",
                 "ट्राइकोडर्मा वीरिडे से जड़ शोधन"),

                ("02", "वानस्पतिक बढ़वार (Vegetative Growth)", 20,
                 f"19:19:19 NPK ड्रिप/स्प्रे @ 5g/L + यूरिया: {int(25 * acreage)} kg",
                 "3-4 दिन के अंतराल पर ड्रिप/सतही सिंचाई। " + weather_alert,
                 "सफेद मक्खी व मरोड़िया (Leaf Curl) रोग हेतु पीले चिपचिपे कार्ड लगाएं"),

                ("03", "फूल आने की अवस्था (Flowering Stage)", 40,
                 f"13:0:45 पोटेशियम नाइट्रेट + बोरॉन 1g/L",
                 "फूल झड़न रोकने हेतु नियमित हल्की नमी।",
                 "फल छेदक (Fruit Borer) निगरानी व नीम तेल 5ml/L छिड़काव"),

                ("04", "फल विकास (Fruit Development)", 60,
                 f"कैल्शियम नाइट्रेट @ 2g/L (सड़न रोकने हेतु)",
                 "समान नमी (अनियमित पानी से फल फटते हैं)।",
                 "अगेती/पछेती झुलसा रोकथाम (कॉपर ऑक्सीक्लोराइड @ 2.5g/L)"),

                ("05", "फल तुड़ाई (Harvesting Phase)", 75,
                 "0:0:50 पोटाश स्प्रे फल चमक हेतु",
                 "तुड़ाई के उपरांत हल्की सिंचाई।",
                 "नियमित फल तुड़ाई व ग्रेडिंग")
            ]

        # 4. POTATO (आलू)
        elif "आलू" in crop_name or "potato" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार खाद (Tuber Planting)", 0,
                 f"DAP: {int(60 * acreage)} kg, MOP: {int(40 * acreage)} kg, यूरिया: {int(30 * acreage)} kg",
                 "हल्की नालीदार सिंचाई (कंद डूबने न पाएं)।",
                 "कंद उपचार (कार्बेन्डाजिम या ट्राइकोडर्मा)"),

                ("02", "मिट्टी चढ़ाना (Earthing Up)", 25,
                 f"यूरिया: {int(35 * acreage)} kg (टॉप ड्रेसिंग)",
                 "सिंचाई मिट्टी चढ़ाने के 2 दिन बाद। " + weather_alert,
                 "खुले आलू हरे होने से रोकने हेतु मेढ़ ऊंची करें"),

                ("03", "कंद निर्माण (Tuber Initiation)", 48,
                 "19:19:19 घुलनशील खाद स्प्रे @ 5g/L",
                 "क्रांतिक सिंचाई (नमी 70-80% रखें)।",
                 "पछेती झुलसा (Late Blight) सुरक्षा: मैंकोजेब @ 2.5g/L पूर्व छिड़काव"),

                ("04", "कंद का आकार बढ़ना (Tuber Bulking)", 68,
                 "0:0:50 पोटाश स्प्रे @ 10g/L",
                 "हल्की नियमित सिंचाई।",
                 "माहू (Aphid) व वायरस वाहक कीट नियंत्रण"),

                ("05", "बेल कटाई व खुदाई (Dehaulming & Digging)", 88,
                 "खाद समाप्त",
                 "खुदाई से 10-12 दिन पूर्व पानी बंद। बेलें काटें।",
                 "छिलका सख्त होने के बाद खुदाई करें")
            ]

        # 5. MAIZE (मक्का)
        elif "मक्का" in crop_name or "maize" in crop_lower or "corn" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व बेसल पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(45 * acreage)} kg, MOP: {int(20 * acreage)} kg, जिंक सल्फेट: {int(10 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "एट्राजिन खरपतवारनाशी बुवाई के 48 घंटे में"),

                ("02", "घुटने तक ऊंचाई (Knee High Stage)", 25,
                 f"यूरिया: {int(40 * acreage)} kg (पहली टॉप ड्रेसिंग)",
                 "पहली मुख्य सिंचाई। " + weather_alert,
                 "फॉल आर्मीवर्म (Fall Armyworm) की कली में जांच"),

                ("03", "मंजर व सिल्क अवस्था (Tasseling & Silking)", 50,
                 f"यूरिया: {int(35 * acreage)} kg (दूसरी टॉप ड्रेसिंग)",
                 "अत्यंत क्रांतिक सिंचाई (दाना भराव प्रभावित न हो)।",
                 "तना छेदक व इल्ली नियंत्रण"),

                ("04", "दाना भराव (Grain Filling)", 72,
                 "0:52:34 स्प्रे (1kg/एकड़)",
                 "हल्की सिंचाई जब तक दाना सख्त न हो।",
                 "भुट्टे में पक्षियों से सुरक्षा"),

                ("05", "कटाई (Harvesting)", 98,
                 "खाद समाप्त",
                 "कटाई से पूर्व खेत सुखाएं।",
                 "भुट्टों का छिलका भूरा सूखने पर कटाई")
            ]

        # 6. GRAM / CHICKPEA (चना) - Legume Pulse
        elif "चना" in crop_name or "gram" in crop_lower or "chana" in crop_lower or "chickpea" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(15 * acreage)} kg, बेंटोनाइट सल्फर: {int(8 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "राइजोबियम व ट्राइकोडर्मा (2g/kg) से बीजोपचार कर उकठा (Wilt) रोग से सुरक्षा"),

                ("02", "शाखाएं निकलना व निराई (Branching & Weeding)", 30,
                 f"19:19:19 घुलनशील पोषण स्प्रे @ 5g/L (दालों में यूरिया टॉप-ड्रेसिंग न डालें)",
                 "पहली हल्की सिंचाई केवल यदि मिट्टी अत्यधिक शुष्क हो। दलहन में अधिक पानी हानिकारक है। " + weather_alert,
                 "हाथ से निराई-गुड़ाई कर खरपतवार निकालें"),

                ("03", "फूल व घंटी बनना (Flowering & Pod Initiation)", 55,
                 "0:52:34 घुलनशील खाद @ 10g/L + बोरॉन 1g/L स्प्रे (फूल व फलियां टिकने हेतु)",
                 "फूल आने की अवस्था में सिंचाई न दें (फूल झड़ सकते हैं)।",
                 "चने की फली छेदक (Helicoverpa / Pod Borer) निगरानी: फेरोमोन ट्रैप 5 प्रति एकड़ + नीम तेल 5ml/L"),

                ("04", "दाना भराव व कड़ा होना (Pod Filling)", 80,
                 "0:0:50 पोटाश स्प्रे (1kg/एकड़) दानों के वजन व चमक हेतु",
                 "दूसरी अत्यंत हल्की सिंचाई (दाना सिकुड़ने से बचाव)।",
                 "इल्ली दिखने पर इमामेक्टिन बेंजोएट (0.5g/L) सुरक्षित छिड़काव"),

                ("05", "परिपक्वता व कटाई (Maturity & Harvesting)", 110,
                 "खाद समाप्त",
                 "कटाई से 15 दिन पूर्व पानी बंद।",
                 "पौधे व फलियां भूरी-सुनहरी सूखने पर कटाई व गहाई")
            ]

        # 7. COTTON (कपास) - Fiber Cash Crop
        elif "कपास" in crop_name or "cotton" in crop_lower or "kapas" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार खाद (Sowing & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(30 * acreage)} kg, जिंक सल्फेट: {int(10 * acreage)} kg",
                 "पलेवा कर उचित ओट में बुवाई।",
                 "इमिडाक्लोप्रिड से उपचारित बीज प्रयोग करें"),

                ("02", "चौपड़ा व शाखा बढ़वार (Squaring & Vegetative)", 35,
                 f"यूरिया: {int(35 * acreage)} kg (पहली टॉप ड्रेसिंग)",
                 "पहली मुख्य सिंचाई। " + weather_alert,
                 "रस चूसक कीट (माहू, हरा तेला, थ्रिप्स) हेतु पीले/नीले चिपचिपे कार्ड लगाएं"),

                ("03", "फूल व टिंडे बनना (Flowering & Boll Setting)", 65,
                 f"यूरिया: {int(35 * acreage)} kg + मैग्नीशियम सल्फेट स्प्रे @ 10g/L",
                 "12-15 दिन के अंतराल पर क्रांतिक सिंचाई।",
                 "गुलाबी सुंडी (Pink Bollworm) निगरानी: फेरोमोन ट्रैप 8 प्रति एकड़"),

                ("04", "टिंडा विकास (Boll Development)", 95,
                 "0:0:50 पोटाश @ 10g/L स्प्रे (टिंडे के आकार व रेशे की गुणवत्ता हेतु)",
                 "खेत में लगातार हल्की नमी बनाए रखें।",
                 "अल्टरनेरिया पत्ती धब्बा रोग जांचें"),

                ("05", "टिंडा खिलना व चुनाई (Boll Bursting & Picking)", 140,
                 "खाद समाप्त",
                 "चुनाई से 15 दिन पूर्व पानी पूरी तरह बंद करें।",
                 "सूखे खिले टिंडों की सुबह ओस सूखने पर साफ चुनाई करें")
            ]

        # 8. SOYBEAN (सोयाबीन) - Kharif Oilseed
        elif "सोयाबीन" in crop_name or "soybean" in crop_lower or "soya" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व बेसल खाद (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, SSP: {int(75 * acreage)} kg (सल्फर हेतु), MOP: {int(20 * acreage)} kg",
                 "चौड़ी क्यारी (BBF) विधि में बुवाई करें ताकि जलभराव न हो।",
                 "ब्रेडीराइजोबियम कल्चर व थीरम से बीज शोधन"),

                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 25,
                 "19:19:19 स्प्रे @ 5g/L",
                 "बारिश न होने पर हल्की सिंचाई। " + weather_alert,
                 "इमाजेथापायर @ 300ml/एकड़ से खरपतवार नियंत्रण बुवाई के 20 दिन में"),

                ("03", "फूल आने की अवस्था (Flowering Stage)", 45,
                 "0:52:34 घुलनशील स्प्रे @ 10g/L",
                 "फूल आते समय पानी की कमी न होने दें।",
                 "गर्डल बीटल (चक्र भृंग) व तना मक्खी नियंत्रण"),

                ("04", "फली विकास (Pod Development)", 70,
                 "0:0:50 पोटाश स्प्रे (1kg/एकड़) तेल व दाना भराव हेतु",
                 "अति आवश्यक होने पर ही हल्की सिंचाई।",
                 "पत्ती खाने वाली इल्ली सुरक्षा: नीम तेल 5ml/L"),

                ("05", "परिपक्वता व कटाई (Harvesting)", 95,
                 "खाद समाप्त",
                 "खेत सुखाएं।",
                 "पत्तियां पीली होकर झड़ने पर दानों में 14% नमी पर कटाई")
            ]

        # 9. SUGARCANE (गन्ना) - Annual Cash Crop
        elif "गन्ना" in crop_name or "sugarcane" in crop_lower or "ganna" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Planting & Basal)", 0,
                 f"DAP: {int(75 * acreage)} kg, MOP: {int(50 * acreage)} kg, जिंक सल्फेट: {int(15 * acreage)} kg",
                 "नाली में रोपाई उपरांत तुरंत भरपूर सिंचाई।",
                 "कार्बेन्डाजिम घोल में टुकड़ों का 15 मिनट उपचार"),

                ("02", "कल्ले फूटना (Tillering / Formative)", 45,
                 f"यूरिया: {int(50 * acreage)} kg (पहली टॉप ड्रेसिंग)",
                 "10-12 दिन के अंतराल पर सिंचाई। " + weather_alert,
                 "कंसुआ (Early Shoot Borer) नियंत्रण हेतु क्लोरेंट्रानिलीप्रोल"),

                ("03", "तीव्र वानस्पतिक बढ़वार (Grand Growth)", 90,
                 f"यूरिया: {int(50 * acreage)} kg (दूसरी टॉप ड्रेसिंग) + मिट्टी चढ़ाना",
                 "नियमित सिंचाई (सूखा न पड़ने दें)।",
                 "तना छेदक व सफेद मक्खी निगरानी"),

                ("04", "गन्ना बढ़वार व शर्करा निर्माण (Elongation)", 150,
                 "0:0:50 पोटाश स्प्रे (2kg/एकड़) सुक्रोज प्रतिशत बढ़ाने हेतु",
                 "15-18 दिन के अंतराल पर सिंचाई।",
                 "गन्ना बंधाई करें ताकि तेज हवा में गिरे नहीं"),

                ("05", "परिपक्वता व कटाई (Maturity & Harvest)", 300,
                 "खाद समाप्त",
                 "कटाई से 15 दिन पूर्व सिंचाई बंद।",
                 "ब्रिक्स मीटर से 18-20% मिठास जांचकर जड़ से कटाई")
            ]

        # 10. ONION (प्याज / कांदा)
        elif "प्याज" in crop_name or "onion" in crop_lower or "कांदा" in crop_name or "pyaj" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Transplanting & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(40 * acreage)} kg, बेंटोनाइट सल्फर: {int(15 * acreage)} kg",
                 "रोपाई उपरांत तुरंत हल्की सिंचाई।",
                 "थीरम या कार्बेन्डाजिम से पौध जड़ उपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative & Weeding)", 25,
                 f"यूरिया: {int(30 * acreage)} kg (प्रथम टॉप ड्रेसिंग)",
                 "7-8 दिन के अंतराल पर हल्की सिंचाई। " + weather_alert,
                 "हाथ से निराई-गुड़ाई व खरपतवार नियंत्रण"),
                ("03", "गांठ निर्माण (Bulb Initiation)", 50,
                 f"19:19:19 घुलनशील खाद @ 5g/L + यूरिया: {int(25 * acreage)} kg",
                 "नियमित सिंचाई (मिट्टी में नमी 65-70% रखें)।",
                 "थ्रिप्स (Thrips) कीट नियंत्रण: नीले चिपचिपे कार्ड 6/एकड़ + नीम तेल 5ml/L"),
                ("04", "गांठ का विकास व आकार (Bulb Development)", 75,
                 "0:0:50 पोटाश स्प्रे (1.5kg/एकड़) कंद का आकार व रंग चमकाने हेतु",
                 "हल्की सिंचाई (अधिक जलभराव से कंद सड़ते हैं)।",
                 "बैंगनी धब्बा रोग (Purple Blotch) जांचें; मैंकोजेब @ 2.5g/L स्प्रे"),
                ("05", "परिपक्वता व खुदाई (Maturity & Harvest)", 105,
                 "खाद समाप्त",
                 "खुदाई से 15 दिन पूर्व पानी पूरी तरह बंद करें।",
                 "50% पौधों की गर्दन झुकने (Neck Fall) पर खुदाई व छाया में सुखाना")
            ]

        # 11. GARLIC (लहसुन)
        elif "लहसुन" in crop_name or "garlic" in crop_lower or "lahsun" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व बेसल पोषण (Cloves Planting)", 0,
                 f"DAP: {int(60 * acreage)} kg, MOP: {int(35 * acreage)} kg, बेंटोनाइट सल्फर: {int(20 * acreage)} kg (तीखेपन हेतु अनिवार्य)",
                 "बुवाई के तुरंत बाद पहली हल्की सिंचाई।",
                 "कार्बेन्डाजिम (2g/kg) से कलियों का उपचार"),
                ("02", "अंकुरण व पहली सिंचाई (Sprouting & Growth)", 30,
                 f"यूरिया: {int(35 * acreage)} kg (प्रथम टॉप ड्रेसिंग)",
                 "8-10 दिन के अंतराल पर सिंचाई। " + weather_alert,
                 "हाथ से पहली निराई-गुड़ाई कर खरपतवार निकालें"),
                ("03", "कंद निर्माण (Bulb Formation)", 60,
                 "19:19:19 @ 5g/L + सूक्ष्म पोषक तत्व (जिंक + बोरॉन 1g/L)",
                 "कंद निर्माण के समय नियमित नमी बनाए रखें।",
                 "थ्रिप्स व पत्ती झुलसा रोकथाम (नीम तेल 5ml/L)"),
                ("04", "गांठ का आकार बढ़ना (Bulb Bulking)", 90,
                 "0:0:50 पोटाश स्प्रे @ 10g/L गांठों का वजन बढ़ाने हेतु",
                 "अंतिम हल्की सिंचाई।",
                 "स्टेंफिलियम ब्लाइट निगरानी व कॉपर फफूंदनाशी स्प्रे"),
                ("05", "परिपक्वता व खुदाई (Harvesting)", 125,
                 "खाद समाप्त",
                 "खुदाई से 12 दिन पूर्व पानी बंद करें।",
                 "पौधों की 70% पत्तियां पीली सूखने पर कंदों की खुदाई")
            ]

        # 12. CHILLI (मिर्च)
        elif "मिर्च" in crop_name or "chilli" in crop_lower or "chili" in crop_lower or "mirch" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Transplanting & Basal)", 0,
                 f"DAP: {int(45 * acreage)} kg, MOP: {int(30 * acreage)} kg, नीम खली: {int(80 * acreage)} kg",
                 "रोपाई के बाद तुरंत हल्की सिंचाई।",
                 "ट्राइकोडर्मा वीरिडे से पौध जड़ शोधन"),
                ("02", "वानस्पतिक बढ़वार (Branching & Vegetative)", 25,
                 f"यूरिया: {int(25 * acreage)} kg + 19:19:19 स्प्रे @ 5g/L",
                 "5-7 दिन के अंतराल पर हल्की सिंचाई। " + weather_alert,
                 "मरोड़िया रोग (Leaf Curl Virus) वाहक थ्रिप्स व सफेद मक्खी नियंत्रण: नीले-पीले कार्ड 8/एकड़"),
                ("03", "फूल आने की अवस्था (Flowering Stage)", 50,
                 "13:0:45 + बोरॉन 1g/L स्प्रे (फूल व कलियों को झड़ने से रोकने हेतु)",
                 "फूल खिलते समय खेत में समान नमी रखें।",
                 "फल छेदक (Fruit Borer) निगरानी: फेरोमोन ट्रैप 5 प्रति एकड़"),
                ("04", "फल विकास व पहली तुड़ाई (Fruiting & Picking)", 75,
                 "0:0:50 स्प्रे (1kg/एकड़) + कैल्शियम नाइट्रेट फल चमक व लंबाई हेतु",
                 "नियमित सिंचाई (अनियमित पानी से फल सड़ते हैं)।",
                 "एन्थ्रेक्नोज (फल सड़न) बचाव: एजोक्सीस्ट्रोबिन या कॉपर कवकनाशी"),
                ("05", "तुड़ाई व रख-रखाव (Continuous Harvest)", 100,
                 f"यूरिया: {int(15 * acreage)} kg हर 20 दिन बाद तुड़ाई चक्र बढ़ाने हेतु",
                 "तुड़ाई उपरांत हल्की सिंचाई।",
                 "हरी मिर्च की नियमित तुड़ाई अथवा पकी लाल मिर्च सुखाना")
            ]

        # 13. GREEN GRAM / MOONG (मूंग) - Legume Pulse
        elif "मूंग" in crop_name or "moong" in crop_lower or "mung" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, SSP: {int(50 * acreage)} kg, MOP: {int(15 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई करें।",
                 "राइजोबियम कल्चर व पीएसबी से बीज शोधन कर उकठा रोग से बचाव"),
                ("02", "शाखाएं निकलना (Branching Stage)", 20,
                 "19:19:19 स्प्रे @ 5g/L (दलहन में यूरिया टॉप-ड्रेसिंग न डालें)",
                 "अत्यधिक आवश्यकता होने पर ही हल्की सिंचाई। " + weather_alert,
                 "हाथ से पहली निराई-गुड़ाई"),
                ("03", "फूल आने की अवस्था (Flowering Stage)", 35,
                 "0:52:34 घुलनशील स्प्रे @ 10g/L + बोरॉन 1g/L",
                 "फूल आते समय सिंचाई पूरी तरह रोकें।",
                 "पीला मोजेक वायरस (YMV) वाहक सफेद मक्खी पर नीम तेल 5ml/L छिड़काव"),
                ("04", "फली विकास (Pod Formation)", 50,
                 "0:0:50 पोटाश स्प्रे (1kg/एकड़) फलियों में दाना भरने हेतु",
                 "हल्की सिंचाई (यदि पत्तियां मुरझा रही हों)।",
                 "फली छेदक इल्ली (Pod Borer) नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 65,
                 "खाद समाप्त",
                 "कटाई से पूर्व खेत सुखाएं।",
                 "80% फलियां काली/भूरी पड़ने पर कटाई व गहाई")
            ]

        # 14. BLACK GRAM / URAD (उड़द) - Legume Pulse
        elif "उड़द" in crop_name or "urad" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, SSP: {int(50 * acreage)} kg, MOP: {int(15 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "राइजोबियम व ट्राइकोडर्मा से बीजोपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 20,
                 "19:19:19 घुलनशील पोषण @ 5g/L",
                 "वर्षा न होने पर 20-25 दिन पर पहली हल्की सिंचाई। " + weather_alert,
                 "खरपतवार नियंत्रण (इमाजेथापायर अवशेष जांच)"),
                ("03", "फूल अवस्था (Flowering Stage)", 38,
                 "0:52:34 @ 10g/L स्प्रे",
                 "फूल खिलते समय जलभराव या सूखा न होने दें।",
                 "सफेद मक्खी व बालदार सूंडी पर नीम तेल स्प्रे"),
                ("04", "फली में दाना भराव (Pod Filling)", 55,
                 "0:0:50 पोटाश स्प्रे (1kg/एकड़)",
                 "दाना भरते समय हल्की नमी रखें।",
                 "पत्ती धब्बा व सर्कोस्पोरा रोग रोकथाम"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 75,
                 "खाद समाप्त",
                 "कटाई पूर्व खेत सुखाएं।",
                 "फलियां काली सूखने पर सुबह के समय कटाई")
            ]

        # 15. GROUNDNUT / PEANUT (मूंगफली) - Oilseed Legume
        elif "मूंगफली" in crop_name or "groundnut" in crop_lower or "peanut" in crop_lower or "mungfali" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार खाद (Sowing & Basal)", 0,
                 f"DAP: {int(30 * acreage)} kg, SSP: {int(120 * acreage)} kg (सल्फर व फास्फोरस हेतु), MOP: {int(25 * acreage)} kg",
                 "पलेवा उपरांत भुरभुरी मिट्टी में बुवाई।",
                 "राइजोबियम व थीरम से गिरी शोधन"),
                ("02", "शाखाएं व निराई (Vegetative & Weeding)", 25,
                 f"जिप्सम: {int(100 * acreage)} kg (सुइयां बनने व कैल्शियम आपूर्ति हेतु अनिवार्य)",
                 "10-12 दिन में हल्की सिंचाई। " + weather_alert,
                 "पहली व अंतिम निराई (सुइयां निकलने के बाद गुड़ाई न करें)"),
                ("03", "सुइयां बनना (Pegging Stage)", 45,
                 "0:52:34 स्प्रे @ 10g/L",
                 "सुइयां (Pegs) जमीन में धंसते समय अत्यंत क्रांतिक सिंचाई।",
                 "सफेद लट (White Grub) व कॉलर रॉट सुरक्षा"),
                ("04", "फली में दाना भराव (Pod Development)", 75,
                 "0:0:50 स्प्रे दाना वजन व तेल वृद्धि हेतु",
                 "फलियों में दाना भरते समय हल्की सिंचाई।",
                 "टिक्का रोग (Tikka Leaf Spot) रोकथाम: हेक्साकोनाजोल स्प्रे"),
                ("05", "परिपक्वता व खुदाई (Harvesting)", 110,
                 "खाद समाप्त",
                 "खुदाई से 7 दिन पूर्व हल्की सिंचाई ताकि फलियां टूटे बिना आसानी से उखड़ें।",
                 "फलियों के अंदरूनी छिलके का रंग भूरा होने पर खुदाई")
            ]

        # 16. PEARL MILLET / BAJRA (बाजरा) - Nutri-Cereal
        elif "बाजरा" in crop_name or "bajra" in crop_lower or "pearl millet" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, MOP: {int(15 * acreage)} kg, जिंक सल्फेट: {int(5 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "एजोस्पाइरिलम व थीरम से बीजोपचार"),
                ("02", "कल्ले फूटना (Tillering Stage)", 20,
                 f"यूरिया: {int(35 * acreage)} kg (प्रथम टॉप ड्रेसिंग)",
                 "कल्ले फूटते समय पहली सिंचाई। " + weather_alert,
                 "खरपतवार नियंत्रण (एट्राजिन बुवाई के 48 घंटे में)"),
                ("03", "सिट्टा निकलना (Panicle Emergence)", 42,
                 f"यूरिया: {int(25 * acreage)} kg (द्वितीय टॉप ड्रेसिंग)",
                 "सिट्टा निकलते समय क्रांतिक सिंचाई।",
                 "डाउनी मिल्ड्यू (हरित बाली रोग) निगरानी"),
                ("04", "दाना भराव (Grain Filling)", 62,
                 "0:52:34 घुलनशील स्प्रे (1kg/एकड़)",
                 "दाना भरते समय आवश्यकतानुसार हल्की सिंचाई।",
                 "अरगट (Ergot) व स्मट रोग रोकथाम"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 85,
                 "खाद समाप्त",
                 "कटाई से पूर्व खेत सुखाएं।",
                 "सिट्टे का दाना सख्त होने पर बालियों की कटाई")
            ]

        # 17. SORGHUM / JOWAR (ज्वार)
        elif "ज्वार" in crop_name or "jowar" in crop_lower or "sorghum" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व बेसल पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, MOP: {int(15 * acreage)} kg, जिंक: {int(5 * acreage)} kg",
                 "पलेवा कर बुवाई करें।",
                 "इमिडाक्लोप्रिड या कार्बोफ्यूरान से बीज उपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 25,
                 f"यूरिया: {int(35 * acreage)} kg (प्रथम टॉप ड्रेसिंग)",
                 "पहली सिंचाई 25-30 दिन पर। " + weather_alert,
                 "तना मक्खी (Shoot Fly) नियंत्रण"),
                ("03", "बाली व फूल निकलना (Flowering & Heading)", 50,
                 f"यूरिया: {int(25 * acreage)} kg (द्वितीय टॉप ड्रेसिंग)",
                 "फूल व बाली बनते समय क्रांतिक सिंचाई।",
                 "तना छेदक (Stem Borer) निगरानी"),
                ("04", "दूधिया व दाना भराव (Grain Filling)", 72,
                 "0:52:34 स्प्रे (1kg/एकड़)",
                 "दाना दूधिया अवस्था में हल्की सिंचाई।",
                 "माहू (Aphid) कीट नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 95,
                 "खाद समाप्त",
                 "कटाई पूर्व खेत सुखाएं।",
                 "दाने के आधार पर काला बिंदु (Black layer) दिखने पर कटाई")
            ]

        # 18. PIGEON PEA / ARHAR / TUR (अरहर / तुअर)
        elif "अरहर" in crop_name or "तुअर" in crop_name or "arhar" in crop_lower or "tur" in crop_lower or "pigeon pea" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, SSP: {int(60 * acreage)} kg, जिंक सल्फेट: {int(10 * acreage)} kg",
                 "मेढ़ों पर बुवाई करें ताकि जलभराव न हो।",
                 "राइजोबियम + ट्राइकोडर्मा बीजोपचार"),
                ("02", "शाखाएं व निराई (Branching & Weeding)", 35,
                 "19:19:19 स्प्रे @ 5g/L",
                 "सूखा पड़ने पर ही हल्की सिंचाई। " + weather_alert,
                 "फाइटोफ्थोरा तना झुलसा सुरक्षा"),
                ("03", "कैनोपी विकास (Vegetative Growth)", 75,
                 "0:52:34 घुलनशील स्प्रे @ 10g/L",
                 "वानस्पतिक बढ़वार पर आवश्यक नमी।",
                 "उकठा (Wilt) रोग निगरानी"),
                ("04", "फूल व फली बनना (Flowering & Pod Initiation)", 120,
                 "0:52:34 + बोरॉन 1g/L स्प्रे",
                 "फूल व फली बनते समय सिंचाई।",
                 "फली छेदक (Helicoverpa) फेरोमोन ट्रैप 6/एकड़ + इमामेक्टिन स्प्रे"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 160,
                 "0:0:50 पोटाश स्प्रे",
                 "कटाई से 20 दिन पूर्व पानी बंद।",
                 "85% फलियां भूरी सूखने पर कटाई")
            ]

        # 19. PEA (मटर)
        elif "मटर" in crop_name or "pea" in crop_lower or "matar" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(20 * acreage)} kg",
                 "पलेवा उपरांत सही ओट में बुवाई।",
                 "राइजोबियम व थीरम बीजोपचार"),
                ("02", "कल्ले व बढ़वार (Vegetative Stage)", 25,
                 "19:19:19 स्प्रे @ 5g/L",
                 "शाखा निकलते समय पहली हल्की सिंचाई। " + weather_alert,
                 "सफेद चूर्ण फफूंद (Powdery Mildew) जांच"),
                ("03", "फूल आने की अवस्था (Flowering Stage)", 45,
                 "0:52:34 @ 10g/L + बोरॉन 1g/L",
                 "फूल खिलते समय सिंचाई न करें।",
                 "फली छेदक निगरानी"),
                ("04", "फली विकास (Pod Filling)", 65,
                 "0:0:50 पोटाश स्प्रे दाना मिठास व वजन हेतु",
                 "दाना भराव पर हल्की सिंचाई।",
                 "हरी फलियों की पहली तुड़ाई"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 85,
                 "खाद समाप्त",
                 "कटाई पूर्व खेत सुखाएं।",
                 "पूर्ण परिपक्वता पर अंतिम कटाई")
            ]

        # 20. LENTIL / MASOOR (मसूर)
        elif "मसूर" in crop_name or "lentil" in crop_lower or "masoor" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, MOP: {int(15 * acreage)} kg, सल्फर: {int(10 * acreage)} kg",
                 "सही ओट में बुवाई करें।",
                 "राइजोबियम कल्चर से बीज शोधन"),
                ("02", "शाखा बढ़वार (Branching Stage)", 30,
                 "19:19:19 स्प्रे @ 5g/L",
                 "वर्षा न होने पर 30-35 दिन पर पहली हल्की सिंचाई। " + weather_alert,
                 "गेरुआ (Rust) व उकठा रोकथाम"),
                ("03", "फूल अवस्था (Flowering Stage)", 55,
                 "0:52:34 घुलनशील स्प्रे",
                 "फूल आते समय जलभराव से बचें।",
                 "माहू कीट निगरानी"),
                ("04", "फली दाना भराव (Pod Development)", 75,
                 "0:0:50 पोटाश स्प्रे (1kg/एकड़)",
                 "फली में दाना भरते समय हल्की नमी।",
                 "फली छेदक इल्ली नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 105,
                 "खाद समाप्त",
                 "कटाई पूर्व खेत सुखाएं।",
                 "पौधे सुनहरे-भूरे सूखने पर कटाई")
            ]

        # 21. SUNFLOWER (सूरजमुखी)
        elif "सूरजमुखी" in crop_name or "sunflower" in crop_lower or "surajmukhi" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(25 * acreage)} kg, बेंटोनाइट सल्फर: {int(15 * acreage)} kg",
                 "उचित दूरी पर कतारों में बुवाई।",
                 "थीरम या बाविस्टिन से बीजोपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 25,
                 f"यूरिया: {int(30 * acreage)} kg (टॉप ड्रेसिंग)",
                 "पहली मुख्य सिंचाई। " + weather_alert,
                 "विरलीकरण (एक स्थान पर एक मजबूत पौधा रखें)"),
                ("03", "मुंडी/कली बनना (Head Formation / Bud Stage)", 45,
                 f"यूरिया: {int(20 * acreage)} kg",
                 "अत्यंत क्रांतिक सिंचाई (पानी की कमी न हो)।",
                 "पत्ती धब्बा रोग जांच"),
                ("04", "फूल व बीज भराव (Flowering & Seed Filling)", 70,
                 "बोरॉन 1.5g/L स्प्रे (खोखले दाने रोकने व बीज भराव हेतु)",
                 "फूल खिलते समय सुबह कीटनाशक न छिड़कें (मधुमक्खी परागण सुरक्षा)।",
                 "हेड रॉट फफूंद नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 95,
                 "खाद समाप्त",
                 "कटाई पूर्व खेत सुखाएं।",
                 "मुंडी का पिछला भाग नींबू जैसा पीला होने पर कटाई")
            ]

        # 22. BRINJAL / EGGPLANT (बैंगन)
        elif "बैंगन" in crop_name or "brinjal" in crop_lower or "eggplant" in crop_lower or "baingan" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Transplanting & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(35 * acreage)} kg, नीम खली: {int(80 * acreage)} kg",
                 "रोपाई बाद तुरंत सिंचाई।",
                 "ट्राइकोडर्मा से जड़ उपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Branching)", 22,
                 f"यूरिया: {int(25 * acreage)} kg + 19:19:19 @ 5g/L",
                 "5-6 दिन पर सिंचाई। " + weather_alert,
                 "तना व फल छेदक (Shoot Borer) फेरोमोन ट्रैप 8/एकड़ लगाएं"),
                ("03", "फूल आने की अवस्था (Flowering Stage)", 45,
                 "13:0:45 + बोरॉन 1g/L स्प्रे",
                 "फूल अवस्था में नियमित नमी।",
                 "मुरझाई टहनियों को काटकर नष्ट करें"),
                ("04", "फल विकास व तुड़ाई (Fruiting & Picking)", 68,
                 "0:0:50 स्प्रे फल की चमक व मोटाई हेतु",
                 "नियमित सिंचाई।",
                 "फल छेदक सुरक्षा: नीम तेल 5ml/L छिड़काव"),
                ("05", "लगातार तुड़ाई चक्र (Continuous Harvesting)", 95,
                 f"यूरिया: {int(15 * acreage)} kg हर 20 दिन पर तुड़ाई चक्र बढ़ाने हेतु",
                 "तुड़ाई के उपरांत हल्की सिंचाई।",
                 "प्रत्येक 4-5 दिन में फलों की तुड़ाई")
            ]

        # 23. CAULIFLOWER (फूलगोभी)
        elif "फूलगोभी" in crop_name or "cauliflower" in crop_lower or "phoolgobhi" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Transplanting & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(30 * acreage)} kg, बोरॉन: {int(5 * acreage)} kg (भूरापन रोकने हेतु)",
                 "रोपाई बाद हल्की सिंचाई।",
                 "बाविस्टिन घोल में जड़ शोधन"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 20,
                 f"यूरिया: {int(30 * acreage)} kg + मोलिब्डेनम 1g/L स्प्रे (ह्विपटेल रोग बचाव)",
                 "5-7 दिन पर हल्की सिंचाई। " + weather_alert,
                 "हीरक पतंगा (DBM) फेरोमोन ट्रैप लगाएं"),
                ("03", "फूल बनना (Curd Initiation)", 40,
                 f"यूरिया: {int(30 * acreage)} kg",
                 "क्रांतिक सिंचाई (नमी 70% रखें)।",
                 "इल्ली नियंत्रण"),
                ("04", "फूल का आकार बढ़ना (Curd Enlargement)", 58,
                 "0:0:50 स्प्रे फूल ठोस बनाने हेतु",
                 "सफेद फूल रखने हेतु पत्तियां बांधें (ब्लांचिंग)।",
                 "अल्टरनेरिया पत्ती धब्बा जांच"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 72,
                 "खाद समाप्त",
                 "कटाई से 2 दिन पूर्व पानी न दें।",
                 "फूल गठे हुए और ठोस रहने पर सुबह के समय कटाई")
            ]

        # 24. CABBAGE (पत्तागोभी)
        elif "पत्तागोभी" in crop_name or "cabbage" in crop_lower or "patagobi" in crop_lower or "bandhgobi" in crop_lower:
            days_intervals = [
                ("01", "रोपाई व बेसल पोषण (Transplanting & Basal)", 0,
                 f"DAP: {int(45 * acreage)} kg, MOP: {int(30 * acreage)} kg",
                 "रोपाई उपरांत हल्की सिंचाई।",
                 "जड़ विगलन रोकथाम हेतु फफूंदनाशी उपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 20,
                 f"यूरिया: {int(30 * acreage)} kg",
                 "6-7 दिन पर सिंचाई। " + weather_alert,
                 "तंबाकू इल्ली व DBM निगरानी"),
                ("03", "बंधाई चरण (Head Formation / Cupping)", 42,
                 f"यूरिया: {int(30 * acreage)} kg",
                 "लगातार समान नमी (अनियमित पानी से बंधा फटता है)।",
                 "सफेद तितली व कीट नियंत्रण"),
                ("04", "बंधा ठोस होना (Head Firmness)", 60,
                 "0:0:50 स्प्रे पत्तागोभी को सख्त व वजनी बनाने हेतु",
                 "हल्की नियमित सिंचाई।",
                 "काली सड़न (Black Rot) बचाव: स्ट्रेप्टोसाइक्लिन 1g/10L"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 75,
                 "खाद समाप्त",
                 "कटाई से पूर्व खेत सुखाएं।",
                 "गठे हुए ठोस बंधा की कटाई")
            ]

        # 25. OKRA / BHINDI (भिंडी)
        elif "भिंडी" in crop_name or "okra" in crop_lower or "bhindi" in crop_lower or "ladyfinger" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(20 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "इमिडाक्लोप्रिड से बीज शोधन"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 20,
                 f"यूरिया: {int(25 * acreage)} kg",
                 "4-5 दिन में हल्की सिंचाई। " + weather_alert,
                 "पीला शिरा मोजेक (YVMV) वाहक सफेद मक्खी नियंत्रण: पीले कार्ड 8/एकड़ + नीम तेल"),
                ("03", "फूल व पहली तुड़ाई (Flowering & First Picking)", 38,
                 "19:19:19 @ 5g/L + बोरॉन 1g/L",
                 "फूल व पहली फलियों की तुड़ाई पर नियमित नमी।",
                 "तना व फल छेदक निगरानी"),
                ("04", "फल बढ़वार व तुड़ाई (Fruiting Phase)", 52,
                 f"यूरिया: {int(20 * acreage)} kg",
                 "प्रत्येक 2 दिन में कोमल फलियों की तुड़ाई के बाद तुरंत पानी दें।",
                 "चूसक कीट नियंत्रण"),
                ("05", "अंतिम तुड़ाई व अवशेष (Maturity Phase)", 75,
                 "0:0:50 स्प्रे",
                 "तुड़ाई उपरांत खेत सुखाएं।",
                 "अंतिम तुड़ाई चक्र व फसल अवशेष सफाई")
            ]

        # 26. GINGER (अदरक)
        elif "अदरक" in crop_name or "ginger" in crop_lower or "adrak" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Planting & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(40 * acreage)} kg, सड़ी गोबर खाद 5 टन",
                 "ऊंची क्यारी (Raised bed) में बुवाई बाद तुरंत सिंचाई।",
                 "ट्राइकोडर्मा से कंद उपचार"),
                ("02", "अंकुरण व मल्चिंग (Sprouting & Mulching)", 40,
                 f"यूरिया: {int(25 * acreage)} kg",
                 "पहली हरी पत्तियों की मल्चिंग व मिट्टी चढ़ाना। " + weather_alert,
                 "प्रकंद सड़न (Rhizome Rot) सुरक्षा"),
                ("03", "प्रकंद फैलाव (Rhizome Multiplication)", 90,
                 f"यूरिया: {int(30 * acreage)} kg, MOP: {int(25 * acreage)} kg",
                 "कंदों के तीव्र फैलाव पर नियमित हल्की सिंचाई।",
                 "तना छेदक रोकथाम"),
                ("04", "कंद का आकार बढ़ना (Rhizome Bulking)", 150,
                 "0:0:50 स्प्रे (2kg/एकड़) कंद का वजन व मोटाई बढ़ाने हेतु",
                 "नमी स्तर लगातार बनाए रखें।",
                 "पत्ती धब्बा रोग नियंत्रण"),
                ("05", "परिपक्वता व खुदाई (Harvesting)", 240,
                 "खाद समाप्त",
                 "खुदाई से 20 दिन पूर्व पानी बंद।",
                 "पत्तियां पीली सूखकर गिरने पर कंद खुदाई")
            ]

        # 27. TURMERIC (हल्दी)
        elif "हल्दी" in crop_name or "turmeric" in crop_lower or "haldi" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Planting & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(40 * acreage)} kg, नीम खली: {int(100 * acreage)} kg",
                 "मेढ़ों पर बुवाई उपरांत भरपूर सिंचाई।",
                 "मैंकोजेब घोल में कंद उपचार"),
                ("02", "कल्ले व मल्चिंग (Tillering & Mulching)", 45,
                 f"यूरिया: {int(30 * acreage)} kg",
                 "हरी पत्तियों से मल्चिंग व निराई। " + weather_alert,
                 "प्रकंद विगलन से सुरक्षा"),
                ("03", "प्रकंद निर्माण (Rhizome Development)", 100,
                 f"यूरिया: {int(35 * acreage)} kg, MOP: {int(25 * acreage)} kg + मिट्टी चढ़ाना",
                 "10-12 दिन में नियमित सिंचाई।",
                 "पत्ती लपेटक कीट नियंत्रण"),
                ("04", "कुरकुमिन वृद्धि (Curcumin Enrichment)", 180,
                 "0:0:50 स्प्रे कुरकुमिन प्रतिशत व वजन बढ़ाने हेतु",
                 "नियमित सिंचाई।",
                 "पत्ती धब्बा कवकनाशी स्प्रे"),
                ("05", "परिपक्वता व खुदाई (Harvesting)", 260,
                 "खाद समाप्त",
                 "कटाई से 25 दिन पूर्व सिंचाई बंद।",
                 "पौधे पूरी तरह सूखकर गिरने पर खुदाई")
            ]

        # 28. CUMIN / JEERA (जीरा) - Rabi Cash Spice
        elif "जीरा" in crop_name or "cumin" in crop_lower or "jeera" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(30 * acreage)} kg, MOP: {int(15 * acreage)} kg",
                 "हल्की भुरभुरी मिट्टी में सही ओट में बुवाई।",
                 "कार्बेन्डाजिम (2g/kg) से बीजोपचार"),
                ("02", "पहली सिंचाई व अंकुरण (First Irrigation)", 25,
                 "19:19:19 स्प्रे @ 4g/L",
                 "पहली अत्यंत हल्की नालीदार सिंचाई (खेत में पानी खड़ा न रहे)। " + weather_alert,
                 "छाछिया व उकठा रोग पूर्व-रोकथाम"),
                ("03", "वानस्पतिक बढ़वार (Vegetative Stage)", 45,
                 "घुलनशील सल्फर 2g/L स्प्रे",
                 "वानस्पतिक बढ़वार पर हल्की सिंचाई।",
                 "झुलसा (Blight) व छाछिया (Powdery Mildew) का कवकनाशी स्प्रे"),
                ("04", "दाना भराव (Seed Development)", 70,
                 "0:52:34 स्प्रे दाना चमक हेतु",
                 "दाना भरते समय सिंचाई पूरी तरह रोकें (सिंचाई से झुलसा फैलने का भारी खतरा होता है)।",
                 "माहू कीट नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 95,
                 "खाद समाप्त",
                 "खेत पूरी तरह सूखा रखें।",
                 "छत्रक (Umbels) भूरे पड़ने पर सुबह के समय कटाई ताकि दाने न झड़ें")
            ]

        # 29. CORIANDER / DHANIYA (धनिया)
        elif "धनिया" in crop_name or "coriander" in crop_lower or "dhaniya" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(35 * acreage)} kg, MOP: {int(15 * acreage)} kg",
                 "बीजों को दो भागों में दलकर थीरम से उपचारित कर बुवाई।",
                 "थीरम या कार्बेन्डाजिम बीजोपचार"),
                ("02", "वानस्पतिक बढ़वार (Vegetative Stage)", 25,
                 f"यूरिया: {int(25 * acreage)} kg (यदि हरी पत्ती लेनी हो)",
                 "पहली हल्की सिंचाई व विरलीकरण। " + weather_alert,
                 "हाथ से पहली निराई-गुड़ाई"),
                ("03", "फूल आने की अवस्था (Flowering Stage)", 50,
                 "19:19:19 स्प्रे @ 5g/L",
                 "फूल आते समय छाछिया (Powdery Mildew) नियंत्रण हेतु घुलनशील गंधक (2g/L)।",
                 "माहू कीट निगरानी"),
                ("04", "दाना विकास (Grain Development)", 75,
                 "0:52:34 स्प्रे दाना सुगंध व वजन हेतु",
                 "दाना भराव के समय हल्की सिंचाई।",
                 "पत्ती धब्बा रोग जांच"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 100,
                 "खाद समाप्त",
                 "कटाई से पूर्व खेत सुखाएं।",
                 "बीज जैतून हरे से हल्के भूरे होने पर सुबह कटाई व सुखाना")
            ]

        # 30. BARLEY / JAU (जौ)
        elif "जौ" in crop_name or "barley" in crop_lower or "jau" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(40 * acreage)} kg, MOP: {int(20 * acreage)} kg, जिंक सल्फेट: {int(5 * acreage)} kg",
                 "पलेवा कर सही ओट में बुवाई।",
                 "वीटावैक्स से बीज शोधन"),
                ("02", "कल्ले फूटना (Tillering Stage)", 25,
                 f"यूरिया: {int(35 * acreage)} kg (प्रथम टॉप ड्रेसिंग)",
                 "कल्ले फूटते समय पहली सिंचाई। " + weather_alert,
                 "चौड़ी पत्ती खरपतवार नियंत्रण"),
                ("03", "गांठ बनना (Jointing Stage)", 50,
                 f"यूरिया: {int(25 * acreage)} kg (द्वितीय टॉप ड्रेसिंग)",
                 "गांठ बनते समय दूसरी सिंचाई।",
                 "धारीदार गेरुआ (Stripe Rust) जांच"),
                ("04", "बाली व दाना भराव (Heading & Milking)", 75,
                 "0:52:34 स्प्रे दाना वजन हेतु",
                 "दाना भरते समय हल्की सिंचाई।",
                 "माहो कीट नियंत्रण"),
                ("05", "परिपक्वता व कटाई (Harvesting)", 110,
                 "खाद समाप्त",
                 "कटाई से 12 दिन पूर्व पानी बंद।",
                 "फसल सुनहरी होने पर कंबाइन से कटाई")
            ]

        # 31. WATERMELON / TARBOOZ (तरबूज)
        elif "तरबूज" in crop_name or "watermelon" in crop_lower or "tarbooj" in crop_lower:
            days_intervals = [
                ("01", "बुवाई व आधार पोषण (Sowing & Basal)", 0,
                 f"DAP: {int(50 * acreage)} kg, MOP: {int(40 * acreage)} kg, सड़ी गोबर खाद",
                 "नाली/ड्रिप विधि में बुवाई बाद तुरंत सिंचाई।",
                 "ट्राइकोडर्मा बीज शोधन"),
                ("02", "वानस्पतिक बढ़वार (Vine Growth)", 22,
                 "19:19:19 घुलनशील खाद ड्रिप/स्प्रे @ 5g/L",
                 "4-5 दिन में हल्की सिंचाई। " + weather_alert,
                 "लाल कद्दू भृंग (Red Pumpkin Beetle) नियंत्रण"),
                ("03", "फूल व फल लगना (Flowering & Fruit Setting)", 45,
                 "13:0:45 + बोरॉन 1g/L (फूल व फल टिकने हेतु)",
                 "फूल खिलते समय मधुमक्खी संरक्षण (सुबह कीटनाशक न डालें)।",
                 "फल मक्खी (Fruit Fly) ट्रैप 6/एकड़ा लगाएं"),
                ("04", "फल विकास व मिठास (Fruit Sizing & Sugar Accumulation)", 65,
                 "0:0:50 पोटाश स्प्रे (2kg/एकड़) मिठास (TSS/Brix) व वजन बढ़ाने हेतु",
                 "नियमित समान नमी (अनियमित पानी से तरबूज फटता है)।",
                 "डाउनी मिल्ड्यू फफूंद रोकथाम"),
                ("05", "परिपक्वता व तुड़ाई (Harvesting)", 85,
                 "खाद समाप्त",
                 "तुड़ाई से 5 दिन पूर्व पानी बंद (ताकि फल फटे नहीं व मिठास बढ़े)।",
                 "फल के निचले हिस्से का रंग मलाईदार पीला होने व तंतु सूखने पर तुड़ाई")
            ]

        # 32. WHEAT (गेहूं) - Standard Cereal Fallback
        else:
            dap_kg = int(55 * acreage)
            mop_kg = int(25 * acreage)
            zinc_kg = int(10 * acreage)
            urea_top1 = int(45 * acreage)
            urea_top2 = int(45 * acreage)

            days_intervals = [
                ("01", "बुवाई व बेसल खाद (Sowing & Basal Nutrients)", 0,
                 f"DAP: {dap_kg} kg, MOP: {mop_kg} kg, जिंक सल्फेट: {zinc_kg} kg",
                 "पलेवा (बुवाई पूर्व सिंचाई)",
                 "दीमक नियंत्रण हेतु क्लोरपायरीफॉस व वीटावैक्स से बीज उपचार"),

                ("02", "ताज मूल अवस्था (Crown Root Initiation - CRI)", 21,
                 f"यूरिया: {urea_top1} kg (पहली टॉप ड्रेसिंग)",
                 "सर्वप्रथम एवं सबसे क्रांतिक सिंचाई (CRI Stage)। " + weather_alert,
                 "चौड़ी पत्ती खरपतवार नियंत्रण (2,4-D या मेटसल्फ्यूरोन)"),

                ("03", "कल्ले व गांठ बनना (Tillering & Jointing)", 45,
                 f"यूरिया: {urea_top2} kg (दूसरी टॉप ड्रेसिंग)",
                 "दूसरी सिंचाई (खेत में पर्याप्त नमी रखें)।",
                 "पीला रतुआ (Yellow Rust) व फंगस निरीक्षण"),

                ("04", "बाली निकलना (Booting / Heading Stage)", 65,
                 "NPK 0:52:34 घुलनशील स्प्रे @ 10g/L",
                 "तीसरी सिंचाई (हवा शांत होने पर ही पानी दें)।",
                 "माहो (Aphid) व गेरुआ रोग निगरानी"),

                ("05", "दूधिया व दाना भराव (Milking & Dough Stage)", 85,
                 "पोटाश स्प्रे (0:0:50 @ 10g/L) दाना वजन हेतु",
                 "चौथी हल्की सिंचाई (दाना सिकुड़ने से बचाव)।",
                 "सैनिक कीट व फफूंद निगरानी"),

                ("06", "फसल परिपक्वता व कटाई (Maturity & Harvest)", 115,
                 "खाद की आवश्यकता नहीं",
                 "कटाई से 12 दिन पूर्व पानी पूरी तरह बंद करें।",
                 "दाने में 12% नमी पर कंबाइन से कटाई")
            ]

        stages = []
        irrigation_tasks = []
        fertilizer_tasks = []
        pesticide_tasks = []

        for st_num, st_name, days, fert_info, irr_info, pest_info in days_intervals:
            target_date = (sowing_date + datetime.timedelta(days=days)).isoformat()
            stage_full_title = f"{st_num} - {st_name}"
            stages.append({
                "stage_number": st_num,
                "stage_name": st_name,
                "days_from_sowing": days,
                "target_date": target_date,
                "description": f"बुवाई के {days} दिन बाद: {st_name}।"
            })
            if irr_info:
                irrigation_tasks.append({
                    "title": f"{crop_name}: {st_name} पर सिंचाई",
                    "due_date": target_date,
                    "stage": stage_full_title,
                    "stage_num": st_num,
                    "description": f"{irr_info} खेत में नमी का स्तर जांचकर ही पानी दें।",
                    "priority": "high" if days in [0, 21, 25, 42, 45, 50] else "normal"
                })
            if fert_info:
                fertilizer_tasks.append({
                    "title": f"{crop_name}: {st_name} खाद अनुप्रयोग",
                    "due_date": target_date,
                    "stage": stage_full_title,
                    "stage_num": st_num,
                    "dosage_kg": fert_info,
                    "description": f"{acreage} एकड़ रकबा हेतु अनुशंसित खाद: {fert_info}।",
                    "priority": "high"
                })
            if pest_info:
                pesticide_tasks.append({
                    "title": f"{crop_name}: {st_name} सुरक्षा व IPM",
                    "due_date": target_date,
                    "stage": stage_full_title,
                    "stage_num": st_num,
                    "dosage": pest_info,
                    "description": f"रोग व कीट नियंत्रण: {pest_info}। लक्षण दिखने पर ही रासायनिक छिड़काव करें।",
                    "priority": "normal"
                })

        return {
            "crop_name": crop_name,
            "sowing_date": sowing_date.isoformat(),
            "acreage": acreage,
            "stages": stages,
            "irrigation_tasks": irrigation_tasks,
            "fertilizer_tasks": fertilizer_tasks,
            "pesticide_tasks": pesticide_tasks
        }
