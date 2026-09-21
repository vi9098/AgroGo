import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ml_service import ml_service

def test_ml():
    print("=== TESTING AGRIGO ML & HISTORICAL SERVICES ===")
    
    # 1. Crop Recommender
    print("\n1. Testing AI Crop Recommendation...")
    rec = ml_service.recommend_crop(n=80, p=40, k=40, temp=25.0, humidity=80.0, ph=6.5, rainfall=200.0)
    print("Recommendation output:", rec)
    assert "recommendations" in rec and len(rec["recommendations"]) > 0
    print(" [PASS] Recommended top crop:", rec["top_crop"])

    # 2. Yield Predictor
    print("\n2. Testing AI Yield Prediction (Wheat, Punjab, Bathinda, 5 Acres)...")
    pred = ml_service.predict_yield(
        crop="Wheat", state="Punjab", district="Bathinda", area_acres=5.0
    )
    print("Yield prediction output:", pred)
    assert pred["predicted_harvest"]["total_quintals"] > 0
    print(" [PASS] Predicted total harvest:", pred["predicted_harvest"]["total_quintals"], "Quintals")
    print(" [PASS] Resource water estimate:", pred["resource_requirements"]["water_cubic_meters"], "m3")

    # 3. District Benchmarks
    print("\n3. Testing Official District Benchmarks (Bathinda, Punjab)...")
    bench = ml_service.get_historical_benchmarks(crop="Wheat", state="Punjab", district="Bathinda")
    print("Historical benchmark output:", bench)
    assert bench is not None
    assert bench["avg_yield_tonnes_per_ha"] > 0
    print(f" [PASS] 26-year historical avg yield in Bathinda: {bench['avg_yield_tonnes_per_ha']} Tonnes/Ha")

    # 4. Top district crops
    print("\n4. Testing Top District Crops...")
    top_crops = ml_service.get_top_district_crops(state="Punjab", district="Bathinda", limit=4)
    for tc in top_crops:
        print(f" - {tc['crop']} ({tc['season']}): {tc['avg_yield_tonnes_per_ha']} T/Ha, Avg Prod: {tc['avg_production_tonnes']} T")
    assert len(top_crops) > 0

    print("\n=== ALL ML & HISTORICAL BENCHMARK TESTS PASSED 100%! ===")

if __name__ == "__main__":
    test_ml()
