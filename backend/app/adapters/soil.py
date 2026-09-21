"""
Soil Provider Adapter
Handles soil test reports and soil condition queries.
Strict Rule: NEVER invent soil values. Prompt farmer for soil health card when missing.
"""
import logging
from typing import Dict, Any, Optional
from app.database import query_one

logger = logging.getLogger("agrigo.soil")

class SoilProviderAdapter:
    """Provides verified soil test data or indicates missing records."""

    @classmethod
    def get_farmer_soil_context(cls, farmer_id: str, field_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves stored soil data or explicitly requests a soil test if absent."""
        if field_id:
            record = query_one("SELECT * FROM soil_data WHERE farmer_id = ? AND field_id = ?", (farmer_id, field_id))
        else:
            record = query_one("SELECT * FROM soil_data WHERE farmer_id = ? ORDER BY tested_at DESC", (farmer_id,))

        if record:
            return {
                "has_soil_test": True,
                "soil_type": record["soil_type"],
                "ph": record["ph"],
                "organic_carbon_pct": record["organic_carbon_pct"],
                "npk": {
                    "nitrogen": record["nitrogen_kg_ha"],
                    "phosphorus": record["phosphorus_kg_ha"],
                    "potassium": record["potassium_kg_ha"]
                },
                "moisture_pct": record["moisture_pct"],
                "tested_at": record["tested_at"],
                "recommendation": "Use NPK values to calculate basal fertilizer dose."
            }

        # Do NOT invent values.
        return {
            "has_soil_test": False,
            "soil_type": "Unknown (Soil Test Required)",
            "ph": None,
            "organic_carbon_pct": None,
            "npk": None,
            "moisture_pct": None,
            "message": "आपके खेत का मृदा परीक्षण (Soil Health Card) रिकॉर्ड उपलब्ध नहीं है। कृपया नजदीकी KVK या कृषि केंद्र से मृदा जांच करवाएं ताकि सटीक उर्वरक मात्रा निर्धारित की जा सके।"
        }
