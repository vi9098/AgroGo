import sys
import requests
from pathlib import Path

# Configure utf-8 console output for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ml_endpoints():
    print("=== TESTING AGRIGO ML & STATISTICAL API ENDPOINTS ===")

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    print(" [PASS] /health is healthy")

    # 2. Crop Recommendation Endpoint
    print("\n1. Testing POST /api/v1/agriculture/predict/crop...")
    payload_rec = {
        "n": 80.0,
        "p": 40.0,
        "k": 40.0,
        "temperature": 27.5,
        "humidity": 80.0,
        "ph": 6.8,
        "rainfall": 600.0
    }
    rec_res = client.post("/api/v1/agriculture/predict/crop", json=payload_rec)
    assert rec_res.status_code == 200, f"Failed: {rec_res.text}"
    rec_data = rec_res.json()["data"]
    print(" [PASS] Top recommended crop:", rec_data["top_crop"])
    assert len(rec_data["recommendations"]) > 0

    # 3. Yield Prediction Endpoint
    print("\n2. Testing POST /api/v1/agriculture/predict/yield...")
    payload_yield = {
        "crop": "Wheat",
        "state": "Punjab",
        "district": "Bathinda",
        "area_acres": 4.0
    }
    yield_res = client.post("/api/v1/agriculture/predict/yield", json=payload_yield)
    assert yield_res.status_code == 200, f"Failed: {yield_res.text}"
    y_data = yield_res.json()["data"]
    print(" [PASS] Predicted harvest:", y_data["predicted_harvest"])
    assert y_data["predicted_harvest"]["total_quintals"] > 0
    assert y_data["resource_requirements"]["water_cubic_meters"] > 0

    # 4. District Historical Statistics Endpoint
    print("\n3. Testing GET /api/v1/agriculture/stats/district...")
    stats_res = client.get("/api/v1/agriculture/stats/district?state=Punjab&district=Bathinda&crop=Wheat")
    assert stats_res.status_code == 200, f"Failed: {stats_res.text}"
    s_data = stats_res.json()
    print(" [PASS] Benchmark:", s_data["benchmark"])
    print(f" [PASS] Top crops in Bathinda: {len(s_data['top_cultivated_crops'])} found")
    assert s_data["benchmark"]["avg_yield_tonnes_per_ha"] > 0

    # 5. Geographic Hierarchy
    print("\n4. Testing GET /api/v1/agriculture/geo/hierarchy...")
    geo_res = client.get("/api/v1/agriculture/geo/hierarchy")
    assert geo_res.status_code == 200
    geo_data = geo_res.json()
    print(f" [PASS] States indexed in government database: {geo_data['states_count']}")
    assert geo_data["states_count"] > 10

    # 6. Chat RAG with conversational crop recommendation
    print("\n5. Testing POST /api/v1/chat/ask with Crop Recommendation...")
    chat_rec = client.post("/api/v1/chat/ask", json={
        "question": "मेरी जमीन में कौन सी फसल बोएं? अच्छी पैदावार वाली फसल बताएं",
        "language": "hi",
        "farmer_id": "farmer-1001"
    })
    assert chat_rec.status_code == 200
    chat_rec_data = chat_rec.json()
    print(" [PASS] AI Crop Recommendation Response snippet:")
    print(" ", chat_rec_data["response"][:200].replace("\n", " "))

    # 7. Chat RAG with conversational yield prediction
    print("\n6. Testing POST /api/v1/chat/ask with Yield Prediction...")
    chat_yield = client.post("/api/v1/chat/ask", json={
        "question": "मेरी 5 एकड़ जमीन में गेहूं की कितनी पैदावार हो सकती है?",
        "language": "hi",
        "farmer_id": "farmer-1001"
    })
    assert chat_yield.status_code == 200
    chat_yield_data = chat_yield.json()
    print(" [PASS] AI Yield Prediction Response snippet:")
    print(" ", chat_yield_data["response"][:200].replace("\n", " "))

    print("\n=== ALL ML & GOVERNMENT DATASET INTEGRATION TESTS PASSED 100%! ===")

if __name__ == "__main__":
    test_ml_endpoints()
