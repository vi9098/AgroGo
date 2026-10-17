"""
AgriGo Agricultural Knowledge, Weather, Farmer and Decision Endpoints
Exposes complete REST API suite for crops, weather, market, observations, reminders, and sources.
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import shutil
import os
import uuid
import datetime
import json
import math
import requests

from app.database import query_db, query_one, execute_db
from app.services.agri_knowledge import AgriKnowledgeService, AGROVOC_CROPS, AGROVOC_PROBLEMS
from app.services.agri_rag import AgriRAGService
from app.services.reminder_engine import ReminderEngine
from app.adapters.weather import WeatherProviderAdapter
from app.adapters.soil import SoilProviderAdapter
from app.adapters.market import MarketDataProviderAdapter
from app.adapters.vision import VisionProviderAdapter
from app.services.ml_service import ml_service
from app.middleware.auth import require_auth, verify_farmer_ownership, get_current_user_optional

router = APIRouter(prefix="/api/v1", tags=["Agriculture & Knowledge"])

# ----------------- Models -----------------
class NaturalReminderRequest(BaseModel):
    farmer_id: str
    text: str

class ObservationRequest(BaseModel):
    farmer_id: str
    crop: str
    location: str
    problem: str
    observed_pest: Optional[str] = None
    treatment_applied: Optional[str] = None
    result: Optional[str] = None

class CropCycleCreate(BaseModel):
    farmer_id: str
    field_id: Optional[str] = None
    crop_name: str
    variety: Optional[str] = None
    sowing_date: str
    expected_harvest_date: Optional[str] = None
    area_acres: Optional[float] = 1.0
    irrigation_method: Optional[str] = "Drip"
    soil_type: Optional[str] = "Sandy Loam"

# ----------------- Agriculture APIs -----------------
@router.get("/agriculture/crops")
def get_supported_crops():
    """Returns all AGROVOC crops and critical growth stages."""
    return {"status": "OK", "crops": AGROVOC_CROPS}

@router.get("/agriculture/diseases")
def get_known_diseases():
    """Returns verified agricultural disease concepts."""
    return {"status": "OK", "diseases": AGROVOC_PROBLEMS}

@router.get("/agriculture/weather")
async def get_agri_weather(lat: Optional[float] = None, lon: Optional[float] = None):
    """Hyper-local Open-Meteo agricultural weather and spraying window telemetry."""
    return await WeatherProviderAdapter.get_agricultural_weather(lat, lon)

@router.get("/agriculture/weather/detailed")
async def get_agri_weather_detailed(lat: Optional[float] = None, lon: Optional[float] = None):
    """
    Detailed Open-Meteo agricultural telemetry:
    Current conditions, Next 24h Hourly, Past 10 Days History, 7-Day Forecast,
    Growing Degree Days (GDD), Spray Windows, and Disease Risk Indices.
    """
    return await WeatherProviderAdapter.get_detailed_weather(lat, lon)

# ----------------- Market & Mandi Price Models & Endpoints -----------------
class RevenueCalculationRequest(BaseModel):
    commodity: str
    area_acres: float = 1.0
    expected_yield_qtl_per_acre: Optional[float] = None
    custom_rate_per_qtl: Optional[float] = None
    state: Optional[str] = None

@router.get("/agriculture/market")
@router.get("/agriculture/market/live")
def get_mandi_prices(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Returns verified Mandi market prices (data.gov.in / Agmarknet / eNAM)."""
    res = MarketDataProviderAdapter.get_commodity_prices(
        commodity=commodity,
        state=state,
        district=district,
        limit=limit,
        offset=offset
    )
    return {"status": "OK", **res}

@router.get("/agriculture/market/meta")
def get_mandi_meta():
    """Returns distinct commodities, states, and government MSP benchmarks."""
    return {"status": "OK", **MarketDataProviderAdapter.get_supported_commodities_and_states()}

@router.post("/agriculture/market/sync")
def sync_live_mandi(limit: int = 500, commodity: Optional[str] = None):
    """Triggers background synchronization with data.gov.in Agmarknet API."""
    res = MarketDataProviderAdapter.sync_live_mandi_prices(limit=limit, commodity=commodity)
    return res

@router.post("/agriculture/market/calculate-revenue")
def calculate_crop_revenue(payload: RevenueCalculationRequest):
    """Calculates crop revenue, production, net farmer earnings, and MSP comparison."""
    if not MarketDataProviderAdapter.is_valid_commodity(payload.commodity):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_CROP",
                "message": "अमान्य फसल का नाम (Invalid Crop Name)। कृपया सही फसल का नाम लिखें ताकि सही परिणाम मिल सके (उदा. गेहूं, धान, सरसों, चना, मक्का, टमाटर, आलू, प्याज आदि)।",
                "message_en": "Invalid crop name. Please enter a valid crop name to get accurate market calculation (e.g. Wheat, Mustard, Paddy, Gram, Tomato, etc.)."
            }
        )
    res = MarketDataProviderAdapter.calculate_revenue(
        commodity=payload.commodity,
        area_acres=payload.area_acres,
        expected_yield_qtl_per_acre=payload.expected_yield_qtl_per_acre,
        custom_rate_per_qtl=payload.custom_rate_per_qtl,
        state=payload.state
    )
    if not res.get("valid", True):
        raise HTTPException(
            status_code=400,
            detail={
                "error": res.get("error", "INVALID_CROP"),
                "message": res.get("message", "अमान्य फसल का नाम। कृपया सही फसल का नाम लिखें।"),
                "message_en": res.get("message_en", "Invalid crop name. Please enter a valid crop name.")
            }
        )
    return {"status": "OK", "data": res}

@router.get("/agriculture/soil/{farmer_id}")
def get_farmer_soil(farmer_id: str, field_id: Optional[str] = None, user: Dict[str, Any] = Depends(require_auth)):
    """Retrieves farmer soil test data with IDOR ownership validation."""
    verify_farmer_ownership(user, farmer_id)
    return SoilProviderAdapter.get_farmer_soil_context(farmer_id, field_id)

# ----------------- Farmer Farm Context APIs -----------------
@router.get("/farmer/crops/{farmer_id}")
def get_farmer_crops(farmer_id: str, user: Dict[str, Any] = Depends(require_auth)):
    """Retrieves active crop cycles with IDOR protection (farmer sees only own crops)."""
    verify_farmer_ownership(user, farmer_id)
    cycles = query_db("SELECT * FROM crop_cycles WHERE farmer_id = ? ORDER BY created_at DESC", (farmer_id,))
    enriched = []
    for c in cycles:
        stage_info = AgriKnowledgeService.estimate_crop_stage(c["sowing_date"], c["crop_name"])
        item = dict(c)
        item["calculated_stage"] = stage_info["current_stage"]
        item["stage_hi"] = stage_info["stage_hi"]
        item["age_days"] = stage_info["age_days"]
        enriched.append(item)
    return {"status": "OK", "crops": enriched}

@router.post("/farmer/crops")
async def add_crop_cycle(payload: CropCycleCreate, user: Dict[str, Any] = Depends(require_auth)):
    """Enters a new crop cycle with IDOR prevention, enforcing session identity."""
    target_farmer_id = user["id"] if user.get("role") != "admin" else payload.farmer_id
    verify_farmer_ownership(user, target_farmer_id)

    cid = f"cycle-{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    execute_db("""
        INSERT INTO crop_cycles (id, field_id, farmer_id, crop_name, variety, sowing_date, expected_harvest_date, area_acres, irrigation_method, soil_type, current_stage, health_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Sowing / Early', 'Good', ?)
    """, (cid, payload.field_id, target_farmer_id, payload.crop_name, payload.variety, payload.sowing_date, payload.expected_harvest_date, payload.area_acres, payload.irrigation_method, payload.soil_type, now))

    # Auto-generate adaptive timeline reminders
    reminders = await ReminderEngine.generate_crop_timeline_reminders(target_farmer_id, payload.crop_name, payload.sowing_date)

    return {
        "status": "OK",
        "crop_cycle_id": cid,
        "message": f"{payload.crop_name} फसल सफलतापूर्वक जोड़ी गई। कृषि टाइमलाइन व अनुस्मारक सक्रिय हैं।",
        "reminders_created": len(reminders)
    }

class ReminderCreate(BaseModel):
    farmer_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: str
    reminder_type: Optional[str] = "general"
    priority: Optional[str] = "normal"
    crop_id: Optional[str] = None

@router.get("/farmer/reminders/{farmer_id}")
def get_farmer_reminders(farmer_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Retrieves active reminders for the farmer with graceful guest support."""
    if user:
        verify_farmer_ownership(user, farmer_id)
    rems = query_db("SELECT * FROM reminders WHERE farmer_id = ? ORDER BY is_completed ASC, due_date ASC, created_at DESC", (farmer_id,))
    return {"status": "OK", "reminders": rems}

@router.post("/farmer/reminders")
def create_custom_reminder(payload: ReminderCreate, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Creates a custom agricultural reminder, associating with authenticated or guest farmer ID."""
    target_farmer_id = (user["id"] if user.get("role") != "admin" else (payload.farmer_id or user["id"])) if user else (payload.farmer_id or "farmer-guest")
    if user:
        verify_farmer_ownership(user, target_farmer_id)

    rid = f"rem-{uuid.uuid4().hex[:8]}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    execute_db("""
        INSERT INTO reminders (id, farmer_id, title, description, due_date, is_completed, reminder_type, priority, crop_id, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
    """, (rid, target_farmer_id, payload.title, payload.description, payload.due_date, payload.reminder_type, payload.priority, payload.crop_id, now))
    return {"status": "OK", "id": rid, "message": "अनुस्मारक सफलतापूर्वक जोड़ा गया।"}

@router.put("/farmer/reminders/{reminder_id}/toggle")
def toggle_reminder_status(reminder_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Toggles reminder completion status."""
    rem = query_one("SELECT is_completed, farmer_id FROM reminders WHERE id = ?", (reminder_id,))
    if not rem:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    if user:
        verify_farmer_ownership(user, rem["farmer_id"])

    new_status = 0 if rem["is_completed"] == 1 else 1
    execute_db("UPDATE reminders SET is_completed = ? WHERE id = ?", (new_status, reminder_id))
    return {"status": "OK", "id": reminder_id, "is_completed": new_status}

@router.delete("/farmer/reminders/{reminder_id}")
def delete_reminder(reminder_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Deletes a reminder."""
    rem = query_one("SELECT farmer_id FROM reminders WHERE id = ?", (reminder_id,))
    if not rem:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    if user:
        verify_farmer_ownership(user, rem["farmer_id"])

    execute_db("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    return {"status": "OK", "id": reminder_id, "message": "अनुस्मारक हटाया गया।"}

@router.post("/farmer/reminders/natural")
async def create_natural_reminder(payload: NaturalReminderRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Parses natural language requests with ownership validation and guest support."""
    target_farmer_id = (user["id"] if user.get("role") != "admin" else payload.farmer_id) if user else (payload.farmer_id or "farmer-guest")
    if user:
        verify_farmer_ownership(user, target_farmer_id)

    res = await ReminderEngine.parse_natural_language_reminder(payload.text, target_farmer_id)
    return {"status": "OK", "reminder": res}

class AutoCropScheduleRequest(BaseModel):
    crop_name: str
    sowing_date: str
    acreage: float = 1.0
    farmer_id: Optional[str] = None
    clear_previous: bool = True

@router.post("/farmer/reminders/auto-generate")
async def auto_generate_crop_schedule(payload: AutoCropScheduleRequest, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """
    Automatically generates complete farming lifecycle schedule (irrigation dates, acreage-scaled fertilizer dosages, IPM spray)
    using ICAR package of practices + DeepSeek AI + live weather analysis.
    """
    target_farmer_id = (user["id"] if user.get("role") != "admin" else (payload.farmer_id or user["id"])) if user else (payload.farmer_id or "farmer-guest")
    if user:
        verify_farmer_ownership(user, target_farmer_id)

    schedule = await ReminderEngine.generate_automated_crop_schedule(
        farmer_id=target_farmer_id,
        crop_name=payload.crop_name,
        sowing_date_str=payload.sowing_date,
        acreage=payload.acreage,
        clear_previous=payload.clear_previous
    )
    return {"status": "OK", "schedule": schedule}

@router.delete("/farmer/reminders/clear-all/{farmer_id}")
def clear_all_farmer_reminders(farmer_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Deletes all reminders for a farmer or guest to start fresh."""
    target_farmer_id = (user["id"] if user.get("role") != "admin" else farmer_id) if user else farmer_id
    if user:
        verify_farmer_ownership(user, target_farmer_id)
    execute_db("DELETE FROM reminders WHERE farmer_id = ?", (target_farmer_id,))
    return {"status": "OK", "message": "समस्त अनुस्मारक सफलतापूर्वक हटा दिए गए हैं।"}


@router.post("/farmer/observations")
def submit_observation(payload: ObservationRequest, user: Dict[str, Any] = Depends(require_auth)):
    """Submits farmer observation with identity enforcement."""
    target_farmer_id = user["id"] if user.get("role") != "admin" else payload.farmer_id
    verify_farmer_ownership(user, target_farmer_id)

    obs_id = AgriKnowledgeService.record_farmer_observation(
        target_farmer_id, payload.crop, payload.location, payload.problem,
        payload.observed_pest, payload.treatment_applied, payload.result
    )
    return {
        "status": "OK",
        "observation_id": obs_id,
        "message": "किसान प्रेक्षण सफलतापूर्वक दर्ज किया गया (COMMUNITY_OBSERVATION)।"
    }

# ----------------- Knowledge Sources APIs -----------------
@router.get("/knowledge/sources")
def get_knowledge_sources():
    """Returns the official source registry (ICAR, TNAU, FAO, etc.) with robots and license metadata."""
    sources = AgriKnowledgeService.list_knowledge_sources()
    return {"status": "OK", "count": len(sources), "sources": sources}

# ----------------- Agricultural AI & Vision APIs -----------------
@router.post("/chat/image")
async def analyze_crop_image(file: UploadFile = File(...), crop_hint: Optional[str] = None):
    """Uploads crop leaf image and analyzes symptoms with strict uncertainty communication."""
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis = await VisionProviderAdapter.analyze_crop_image(image_path=file_path, filename=file.filename, crop_hint=crop_hint)
    return {"status": "OK", "filename": file.filename, "analysis": analysis}

# ----------------- AI Crop Recommendation & Yield Prediction APIs -----------------
class CropRecommendationRequest(BaseModel):
    n: float = 60.0
    p: float = 30.0
    k: float = 30.0
    temperature: float = 26.0
    humidity: float = 65.0
    ph: float = 6.8
    rainfall: float = 750.0

class YieldPredictionRequest(BaseModel):
    crop: str
    state: str
    district: Optional[str] = None
    area_acres: float = 1.0
    n: Optional[float] = None
    p: Optional[float] = None
    k: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    ph: Optional[float] = None
    rainfall: Optional[float] = None

@router.post("/agriculture/predict/crop")
def predict_crop_suitability(payload: CropRecommendationRequest):
    """
    Predicts optimal crops based on agro-climatic parameters using AI model trained on 50,765 records.
    """
    res = ml_service.recommend_crop(
        n=payload.n,
        p=payload.p,
        k=payload.k,
        temp=payload.temperature,
        humidity=payload.humidity,
        ph=payload.ph,
        rainfall=payload.rainfall
    )
    return {"status": "OK", "data": res}

@router.post("/agriculture/predict/yield")
def predict_crop_yield(payload: YieldPredictionRequest):
    """
    Predicts expected harvest yield, resource requirements (water, fertilizer, pesticide),
    and historical district benchmarks.
    """
    res = ml_service.predict_yield(
        crop=payload.crop,
        state=payload.state,
        district=payload.district,
        area_acres=payload.area_acres,
        n=payload.n,
        p=payload.p,
        k=payload.k,
        temp=payload.temperature,
        humidity=payload.humidity,
        ph=payload.ph,
        rainfall=payload.rainfall
    )
    return {"status": "OK", "data": res}

@router.get("/agriculture/stats/district")
def get_district_statistics(
    state: str = Query(..., description="State name"),
    district: Optional[str] = Query(None, description="District name"),
    crop: Optional[str] = Query(None, description="Crop name")
):
    """
    Returns official historical production and yield records from the Ministry of Agriculture dataset (455,359 records).
    """
    benchmark = None
    top_crops = []
    if crop:
        benchmark = ml_service.get_historical_benchmarks(crop=crop, state=state, district=district)
    if district:
        top_crops = ml_service.get_top_district_crops(state=state, district=district, limit=6)

    return {
        "status": "OK",
        "state": state,
        "district": district,
        "crop": crop,
        "benchmark": benchmark,
        "top_cultivated_crops": top_crops,
        "source": "Ministry of Agriculture & Farmers Welfare, Directorate of Economics & Statistics"
    }

@router.get("/agriculture/geo/hierarchy")
def get_geo_hierarchy():
    """
    Returns available states and districts for dropdown selectors.
    """
    hierarchy = ml_service.get_supported_states_and_districts()
    return {"status": "OK", "states_count": len(hierarchy), "hierarchy": hierarchy}

# Canonical locations registry for reverse geocoding & verified location queries
LOCATIONS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend-html", "js", "india_locations_complete.json"))
CANONICAL_LOCATIONS: Dict[str, Any] = {}
if os.path.exists(LOCATIONS_PATH):
    try:
        with open(LOCATIONS_PATH, "r", encoding="utf-8") as f:
            CANONICAL_LOCATIONS = json.load(f)
    except Exception:
        pass

def _resolve_canonical_state(state_query: str) -> Optional[str]:
    if not state_query:
        return None
    import re
    q = state_query.strip().lower()
    for s in CANONICAL_LOCATIONS.keys():
        if s.lower() == q or q in s.lower() or s.lower() in q:
            return s
        en_match = re.search(r'\(([^)]+)\)', s)
        if en_match and (en_match.group(1).lower() == q or q in en_match.group(1).lower() or en_match.group(1).lower() in q):
            return s
    return None

def _resolve_canonical_district(state_key: str, district_query: str) -> Optional[str]:
    if not state_key or not district_query or state_key not in CANONICAL_LOCATIONS:
        return None
    dists = CANONICAL_LOCATIONS[state_key]
    q = district_query.strip().lower()
    for d in dists.keys():
        if d.lower() == q or q in d.lower() or d.lower() in q:
            return d
    return None

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("/agriculture/locations/all")
def get_all_canonical_locations():
    """Returns verified dataset of all 36 Indian States/UTs and their corresponding districts."""
    return {
        "status": "OK",
        "total_states": len(CANONICAL_LOCATIONS),
        "total_districts": sum(len(d) for d in CANONICAL_LOCATIONS.values()),
        "locations": CANONICAL_LOCATIONS
    }

@router.get("/agriculture/reverse-geocode")
def reverse_geocode_location(lat: float = Query(...), lon: float = Query(...)):
    """
    Reverse geocodes latitude/longitude into locality, district, state,
    matching against canonical Indian geographic registry with offline nearest-district fallback.
    """
    locality = ""
    raw_state = ""
    raw_district = ""
    display_name = ""

    # 1. Attempt OSM Nominatim reverse geocode with short timeout
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=en,hi"
        r = requests.get(url, headers={"User-Agent": "AgriGo-Platform/2.0 (agri@agrigo.in)", "Accept": "application/json"}, timeout=3.5)
        if r.status_code == 200:
            data = r.json()
            display_name = data.get("display_name", "")
            addr = data.get("address", {})
            raw_state = addr.get("state", "")
            raw_district = addr.get("state_district") or addr.get("district") or addr.get("county") or addr.get("city") or ""
            locality = addr.get("village") or addr.get("town") or addr.get("suburb") or addr.get("city") or ""
    except Exception:
        pass

    matched_state = _resolve_canonical_state(raw_state)
    matched_district = _resolve_canonical_district(matched_state, raw_district) if matched_state else None

    # 2. If match failed (or Nominatim failed/offline), use geographic proximity to find closest verified district
    if not matched_state or not matched_district:
        best_dist = float("inf")
        best_state = None
        best_district_key = None
        for s_key, d_map in CANONICAL_LOCATIONS.items():
            for d_key, d_info in d_map.items():
                d_lat = d_info.get("lat")
                d_lon = d_info.get("lon")
                if d_lat is not None and d_lon is not None:
                    h_dist = _haversine(lat, lon, d_lat, d_lon)
                    if h_dist < best_dist:
                        best_dist = h_dist
                        best_state = s_key
                        best_district_key = d_key
        if best_state and best_district_key:
            matched_state = best_state
            matched_district = best_district_key
            if not locality:
                locality = best_district_key.split('(')[0].strip()

    return {
        "status": "OK",
        "matched_state": matched_state or "उत्तर प्रदेश (Uttar Pradesh)",
        "matched_district": matched_district or "वाराणसी (Varanasi)",
        "locality": locality or "स्थानीय क्षेत्र",
        "display_name": display_name or f"{matched_district}, {matched_state}",
        "lat": lat,
        "lon": lon
    }
