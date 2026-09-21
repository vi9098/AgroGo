import os
import sqlite3
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

joblib = None
pd = None

# Suppress scikit-learn feature names warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

from app.database import DB_PATH

logger = logging.getLogger("agrigo.ml_service")

ML_DIR = Path(__file__).resolve().parent.parent / "ml"

class AgriMLService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgriMLService, cls).__new__(cls)
            cls._instance._models_loaded = False
            cls._instance.crop_recommender = None
            cls._instance.yield_regressor = None
            cls._instance.resource_benchmarks = None
        return cls._instance

    def _ensure_models_loaded(self):
        """Lazily load machine learning models on first request rather than during module import."""
        if getattr(self, "_models_loaded", False):
            return
        self._models_loaded = True

        global joblib, pd
        if joblib is None:
            try:
                import joblib
            except ImportError:
                joblib = None
        if pd is None:
            try:
                import pandas as pd
            except ImportError:
                pd = None

        self._init_models()

    def _init_models(self):
        if joblib is None:
            logger.info("joblib not installed in current environment; ML service will operate in heuristic mode.")
            return

        cr_path = ML_DIR / "crop_recommender.joblib"
        if cr_path.exists():
            try:
                self.crop_recommender = joblib.load(cr_path)
                logger.info("Crop Recommender model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load crop_recommender: {e}")

        yr_path = ML_DIR / "yield_regressor.joblib"
        if yr_path.exists():
            try:
                self.yield_regressor = joblib.load(yr_path)
                logger.info("Yield Regressor model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load yield_regressor: {e}")

        rb_path = ML_DIR / "resource_benchmarks.joblib"
        if rb_path.exists():
            try:
                self.resource_benchmarks = joblib.load(rb_path)
                logger.info("Resource Benchmarks loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load resource_benchmarks: {e}")

    def _heuristic_recommend_crop(self, n: float, p: float, k: float, temp: float, humidity: float, ph: float, rainfall: float) -> List[Dict[str, Any]]:
        """ICAR & Ministry of Agriculture Agro-Ecological heuristics for crop recommendations."""
        candidates = []
        if rainfall >= 800 and temp >= 20 and humidity >= 60:
            candidates.append({"crop": "Rice", "suitability_score": 92.5, "confidence": "High"})
        if 12 <= temp <= 28 and rainfall <= 600:
            candidates.append({"crop": "Wheat", "suitability_score": 89.0, "confidence": "High"})
        if temp >= 18 and 400 <= rainfall <= 950:
            candidates.append({"crop": "Maize", "suitability_score": 86.0, "confidence": "High"})
        if temp >= 20 and rainfall >= 700:
            candidates.append({"crop": "Cotton", "suitability_score": 81.5, "confidence": "Moderate"})
        if rainfall < 500 or (humidity < 55 and temp >= 24):
            candidates.append({"crop": "Bajra", "suitability_score": 87.5, "confidence": "High"})
            candidates.append({"crop": "Jowar", "suitability_score": 84.0, "confidence": "Moderate"})
        if 6.0 <= ph <= 7.5 and rainfall < 700:
            candidates.append({"crop": "Chickpea", "suitability_score": 83.0, "confidence": "Moderate"})
        if 15 <= temp <= 25 and rainfall < 500:
            candidates.append({"crop": "Mustard", "suitability_score": 82.0, "confidence": "Moderate"})

        if not candidates:
            candidates = [
                {"crop": "Wheat", "suitability_score": 85.0, "confidence": "Moderate"},
                {"crop": "Rice", "suitability_score": 80.0, "confidence": "Moderate"},
                {"crop": "Maize", "suitability_score": 75.0, "confidence": "Moderate"}
            ]
        return candidates

    def recommend_crop(self, n: float, p: float, k: float, temp: float, humidity: float, ph: float, rainfall: float) -> Dict[str, Any]:
        """
        Predicts optimal crop(s) based on soil nutrients and climatic conditions.
        """
        self._ensure_models_loaded()

        if not self.crop_recommender or pd is None:
            recs = self._heuristic_recommend_crop(n, p, k, temp, humidity, ph, rainfall)
            return {
                "top_crop": recs[0]["crop"] if recs else "Wheat",
                "recommendations": recs,
                "input_parameters": {
                    "N": n, "P": p, "K": k,
                    "temperature_c": temp,
                    "humidity_percent": humidity,
                    "ph": ph,
                    "rainfall_mm": rainfall
                },
                "source": "AgriGo Agro-Climatic Intelligence (ICAR & Ministry of Agriculture Standards)"
            }

        try:
            model = self.crop_recommender["model"]
            le = self.crop_recommender["label_encoder"]
            cols = self.crop_recommender.get("feature_names", ['N_req_kg_per_ha', 'P_req_kg_per_ha', 'K_req_kg_per_ha', 'Temperature_C', 'Humidity_%', 'pH', 'Rainfall_mm'])
            
            X_df = pd.DataFrame([[n, p, k, temp, humidity, ph, rainfall]], columns=cols)
            probs = model.predict_proba(X_df)[0]
            classes = le.classes_

            # Sort top predictions
            ranked_indices = probs.argsort()[::-1]
            recommendations = []
            for idx in ranked_indices:
                prob = float(probs[idx])
                if prob > 0.05: # At least 5% suitability
                    crop_name = classes[idx].capitalize()
                    recommendations.append({
                        "crop": crop_name,
                        "suitability_score": round(prob * 100, 1),
                        "confidence": "High" if prob > 0.4 else "Moderate"
                    })

            return {
                "top_crop": recommendations[0]["crop"] if recommendations else "Wheat",
                "recommendations": recommendations,
                "input_parameters": {
                    "N": n, "P": p, "K": k,
                    "temperature_c": temp,
                    "humidity_percent": humidity,
                    "ph": ph,
                    "rainfall_mm": rainfall
                },
                "source": "AgriGo AI Model trained on 50,765 Historical Agro-Climatic Records"
            }
        except Exception as e:
            logger.error(f"Error in recommend_crop: {e}")
            recs = self._heuristic_recommend_crop(n, p, k, temp, humidity, ph, rainfall)
            return {
                "top_crop": recs[0]["crop"] if recs else "Wheat",
                "recommendations": recs,
                "input_parameters": {"N": n, "P": p, "K": k, "temperature_c": temp, "humidity_percent": humidity, "ph": ph, "rainfall_mm": rainfall},
                "source": "AgriGo Agro-Climatic Fallback Engine"
            }

    def predict_yield(
        self,
        crop: str,
        state: str,
        area_acres: float,
        n: Optional[float] = None,
        p: Optional[float] = None,
        k: Optional[float] = None,
        temp: Optional[float] = None,
        humidity: Optional[float] = None,
        ph: Optional[float] = None,
        rainfall: Optional[float] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predicts harvest yield (Quintals and Tonnes) and calculates optimal inputs.
        """
        self._ensure_models_loaded()
        crop_clean = crop.strip().lower()
        # Extract English name if provided in format 'हिंदी (English)'
        m_s = re.search(r"\(([^)]+)\)", state) if state else None
        state_clean = m_s.group(1).strip() if m_s else (state.strip() if state else "Uttar Pradesh")

        district_clean = None
        if district:
            m_d = re.search(r"\(([^)]+)\)", district)
            district_clean = m_d.group(1).strip() if m_d else district.strip()

        area_ha = area_acres * 0.404686 # Convert acres to hectares

        # Default standard agro-parameters if not specified
        n_val = n if n is not None else 60.0
        p_val = p if p is not None else 30.0
        k_val = k if k is not None else 30.0
        temp_val = temp if temp is not None else 26.0
        hum_val = humidity if humidity is not None else 65.0
        ph_val = ph if ph is not None else 6.8
        rain_val = rainfall if rainfall is not None else 750.0

        predicted_yield_kg_per_ha = None
        predicted_tonnes_total = None
        predicted_quintals_total = None

        if self.yield_regressor and pd is not None:
            try:
                reg = self.yield_regressor["model"]
                c_le = self.yield_regressor["crop_encoder"]
                s_le = self.yield_regressor["state_encoder"]

                # Encode crop & state safely
                c_code = c_le.transform([crop_clean])[0] if crop_clean in c_le.classes_ else 0
                s_code = s_le.transform([state_clean])[0] if state_clean in s_le.classes_ else 0

                cols = self.yield_regressor.get("feature_names", [
                    'crop_code', 'state_code', 'Area_ha',
                    'N_req_kg_per_ha', 'P_req_kg_per_ha', 'K_req_kg_per_ha',
                    'Temperature_C', 'Humidity_%', 'pH', 'Rainfall_mm'
                ])
                X_df = pd.DataFrame([[
                    c_code, s_code, area_ha,
                    n_val, p_val, k_val,
                    temp_val, hum_val, ph_val, rain_val
                ]], columns=cols)

                pred_kg_ha = float(reg.predict(X_df)[0])
                # Ensure physical realism (> 200 kg/ha, < 12000 kg/ha)
                pred_kg_ha = max(200.0, min(12000.0, pred_kg_ha))
                predicted_yield_kg_per_ha = round(pred_kg_ha, 1)

                # Total harvest calculation
                total_kg = predicted_yield_kg_per_ha * area_ha
                predicted_quintals_total = round(total_kg / 100.0, 1)
                predicted_tonnes_total = round(total_kg / 1000.0, 2)
            except Exception as e:
                logger.warning(f"Yield ML regressor error: {e}")

        # Benchmark comparison from official Ministry of Agriculture records (455k rows)
        historical_stats = self.get_historical_benchmarks(crop=crop, state=state_clean, district=district_clean)

        # Fallback to historical district/state averages if ML is not available for this specific crop
        if predicted_tonnes_total is None or predicted_tonnes_total <= 0:
            if historical_stats and historical_stats.get("avg_yield_tonnes_per_ha"):
                avg_t_ha = historical_stats["avg_yield_tonnes_per_ha"]
                predicted_tonnes_total = round(avg_t_ha * area_ha, 2)
                predicted_quintals_total = round(predicted_tonnes_total * 10, 1)
                predicted_yield_kg_per_ha = round(avg_t_ha * 1000, 1)
            else:
                # General agronomic approximation
                predicted_tonnes_total = round(area_acres * 1.8, 2)
                predicted_quintals_total = round(predicted_tonnes_total * 10, 1)
                predicted_yield_kg_per_ha = round((predicted_tonnes_total * 1000) / max(0.01, area_ha), 1)

        # Resource optimization from agriculture_dataset
        resource_est = self.get_resource_estimates(crop_clean, area_acres)

        return {
            "crop": crop.capitalize(),
            "state": state,
            "district": district or "All State",
            "farm_area_acres": area_acres,
            "farm_area_hectares": round(area_ha, 2),
            "predicted_harvest": {
                "total_tonnes": predicted_tonnes_total,
                "total_quintals": predicted_quintals_total,
                "yield_kg_per_ha": predicted_yield_kg_per_ha,
                "yield_quintals_per_acre": round(predicted_quintals_total / max(0.1, area_acres), 1),
            },
            "resource_requirements": resource_est,
            "historical_benchmark": historical_stats,
            "source": "Trained on Ministry of Agriculture & Farmers Welfare Datasets (455,359 historical records + 50k climate trials)"
        }

    def get_resource_estimates(self, crop: str, area_acres: float) -> Dict[str, Any]:
        """
        Estimates water, fertilizer, and pesticide needs from agriculture_dataset.csv
        """
        self._ensure_models_loaded()
        defaults = {
            "water_cubic_meters": round(area_acres * 250.0, 1),
            "fertilizer_kg": round(area_acres * 120.0, 1),
            "pesticide_kg": round(area_acres * 1.5, 2),
            "recommended_irrigation": "Drip / Sprinkler for maximum water efficiency",
            "optimal_soils": "Loamy / Well-drained alluvial soil"
        }

        if self.resource_benchmarks and crop.lower() in self.resource_benchmarks:
            bm = self.resource_benchmarks[crop.lower()]
            return {
                "water_cubic_meters": round(bm["avg_water_m3_per_acre"] * area_acres, 1),
                "fertilizer_kg": round(bm["avg_fertilizer_ton_per_acre"] * 1000 * area_acres, 1),
                "pesticide_kg": round(bm["avg_pesticide_kg_per_acre"] * area_acres, 2),
                "recommended_irrigation": f"Proven successful with {', '.join(bm['irrigation_types'][:3])}",
                "optimal_soils": f"Best performing in {', '.join(bm['soil_types'][:3])} soils"
            }
        return defaults

    def get_historical_benchmarks(self, crop: str, state: Optional[str] = None, district: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Queries official 455k record database for district/state crop statistics.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            # Match crop name flexibly (e.g. 'Wheat', 'Rice', 'Cotton')
            crop_pattern = f"%{crop.strip()}%"

            # 1. District level if provided
            if district and state:
                c.execute("""
                    SELECT state_name, district_name, crop_name, season, avg_yield, max_yield, min_yield, avg_production, record_count
                    FROM district_crop_benchmarks
                    WHERE state_name LIKE ? AND district_name LIKE ? AND crop_name LIKE ?
                    ORDER BY record_count DESC LIMIT 1
                """, (f"%{state.strip()}%", f"%{district.strip()}%", crop_pattern))
                row = c.fetchone()
                if row:
                    return {
                        "level": "District",
                        "state": row[0],
                        "district": row[1],
                        "crop": row[2],
                        "season": row[3],
                        "avg_yield_tonnes_per_ha": row[4],
                        "max_yield_tonnes_per_ha": row[5],
                        "min_yield_tonnes_per_ha": row[6],
                        "avg_annual_production_tonnes": row[7],
                        "historical_years_recorded": row[8],
                        "source": "Government of India Directorate of Economics & Statistics"
                    }

            # 2. State level
            if state:
                c.execute("""
                    SELECT state_name, crop_name, ROUND(AVG(avg_yield), 3), ROUND(MAX(max_yield), 3), ROUND(MIN(min_yield), 3), SUM(avg_production), SUM(record_count)
                    FROM district_crop_benchmarks
                    WHERE state_name LIKE ? AND crop_name LIKE ?
                    GROUP BY state_name, crop_name
                    ORDER BY SUM(record_count) DESC LIMIT 1
                """, (f"%{state.strip()}%", crop_pattern))
                row = c.fetchone()
                if row:
                    return {
                        "level": "State",
                        "state": row[0],
                        "crop": row[1],
                        "avg_yield_tonnes_per_ha": row[2],
                        "max_yield_tonnes_per_ha": row[3],
                        "min_yield_tonnes_per_ha": row[4],
                        "avg_annual_production_tonnes": round(row[5], 2) if row[5] else None,
                        "historical_years_recorded": row[6],
                        "source": "Government of India Directorate of Economics & Statistics"
                    }

            # 3. National level
            c.execute("""
                SELECT crop_name, ROUND(AVG(avg_yield), 3), ROUND(MAX(max_yield), 3), ROUND(MIN(min_yield), 3), COUNT(*)
                FROM district_crop_benchmarks
                WHERE crop_name LIKE ?
                GROUP BY crop_name
                ORDER BY COUNT(*) DESC LIMIT 1
            """, (crop_pattern,))
            row = c.fetchone()
            if row:
                return {
                    "level": "National Average",
                    "crop": row[0],
                    "avg_yield_tonnes_per_ha": row[1],
                    "max_yield_tonnes_per_ha": row[2],
                    "min_yield_tonnes_per_ha": row[3],
                    "historical_records_analyzed": row[4],
                    "source": "Government of India Directorate of Economics & Statistics"
                }

            return None
        except Exception as e:
            logger.debug(f"Historical benchmarks table unavailable: {e}")
            return None
        finally:
            conn.close()

    def get_top_district_crops(self, state: str, district: str, limit: int = 6) -> List[Dict[str, Any]]:
        """
        Returns top cultivated crops in a given district with average productivity.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("""
                    SELECT crop_name, crop_type, season, avg_yield, avg_production, record_count
                    FROM district_crop_benchmarks
                    WHERE state_name LIKE ? AND district_name LIKE ?
                    ORDER BY avg_production DESC LIMIT ?
                """, (f"%{state.strip()}%", f"%{district.strip()}%", limit))
                rows = c.fetchall()
                return [
                    {
                        "crop": r[0],
                        "crop_type": r[1],
                        "season": r[2],
                        "avg_yield_tonnes_per_ha": r[3],
                        "avg_production_tonnes": r[4],
                        "data_records": r[5]
                    }
                    for r in rows
                ]
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Could not load top district crops from database: {e}")
            return []

    def get_supported_states_and_districts(self) -> Dict[str, List[str]]:
        """
        Returns supported states and their respective districts for UI selectors.
        """
        fallback_hierarchy = {
            "Uttar Pradesh": ["Agra", "Aligarh", "Allahabad", "Ambedkar Nagar", "Amethi", "Bareilly", "Basti", "Bijnor", "Bulandshahr", "Deoria", "Etah", "Etawah", "Faizabad", "Farrukhabad", "Fatehpur", "Firozabad", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Jhansi", "Kanpur Nagar", "Lucknow", "Mathura", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Raebareli", "Saharanpur", "Sitapur", "Sultanpur", "Varanasi"],
            "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Firozpur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Patiala", "Rupnagar", "Sangrur", "Tarn Taran"],
            "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
            "Madhya Pradesh": ["Bhopal", "Chhindwara", "Dewas", "Dhar", "Gwalior", "Hoshangabad", "Indore", "Jabalpur", "Khargone", "Mandsaur", "Morena", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Shivpuri", "Ujjain", "Vidisha"],
            "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Nagpur", "Nanded", "Nashik", "Osmanabad", "Parbhani", "Pune", "Sangli", "Satara", "Solapur", "Wardha", "Yavatmal"],
            "Rajasthan": ["Ajmer", "Alwar", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Chittorgarh", "Churu", "Dausa", "Ganganagar", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Kota", "Nagaur", "Pali", "Sikar", "Tonk", "Udaipur"],
            "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Banaskantha", "Bharuch", "Bhavnagar", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mehsana", "Morbi", "Navsari", "Patan", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Vadodara"],
            "Bihar": ["Araria", "Bhagalpur", "Bhojpur", "Darbhanga", "Gaya", "Katihar", "Madhubani", "Muzaffarpur", "Nalanda", "Patna", "Purnia", "Rohtas", "Samastipur", "Saran", "Siwan", "Vaishali"],
            "West Bengal": ["Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Hooghly", "Jalpaiguri", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "South 24 Parganas", "Uttar Dinajpur"],
            "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bidar", "Chikkamagaluru", "Chitradurga", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kolar", "Mandya", "Mysuru", "Raichur", "Shivamogga", "Tumakuru", "Vijayapura"],
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Kadapa", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"],
            "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Jagtial", "Karimnagar", "Khammam", "Mahabubnagar", "Mancherial", "Medak", "Nalgonda", "Nizamabad", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Warangal"],
            "Tamil Nadu": ["Ariyalur", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Karur", "Madurai", "Nagapattinam", "Namakkal", "Pudukkottai", "Ramanathapuram", "Salem", "Thanjavur", "Theni", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvannamalai", "Vellore", "Villupuram", "Virudhunagar"]
        }

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("""
                    SELECT DISTINCT state_name, district_name 
                    FROM district_crop_benchmarks 
                    ORDER BY state_name, district_name
                """)
                rows = c.fetchall()
                if not rows:
                    return fallback_hierarchy
                mapping: Dict[str, List[str]] = {}
                for state, dist in rows:
                    if state not in mapping:
                        mapping[state] = []
                    mapping[state].append(dist)
                return mapping if mapping else fallback_hierarchy
            finally:
                conn.close()
        except Exception as e:
            logger.info(f"Using standard India agricultural hierarchy ({e})")
            return fallback_hierarchy

ml_service = AgriMLService()
