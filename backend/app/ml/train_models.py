import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

MODELS_DIR = Path(__file__).resolve().parent

def train_crop_recommender():
    """
    Trains a Classifier on agro-environmental features:
    N, P, K, Temperature, Humidity, pH, Rainfall -> Recommended Crop.
    Combines Custom_Crops_yield_Historical_Dataset and agriculture_dataset.
    """
    csv_path = Path(r"C:\Users\raika\Downloads\mynew\Custom_Crops_yield_Historical_Dataset.csv")
    if not csv_path.exists():
        print(f"[WARN] Dataset not found at {csv_path}")
        return None
    
    print("-> Loading Custom_Crops_yield_Historical_Dataset for Crop Recommendation...")
    df = pd.read_csv(csv_path)
    
    # Feature columns
    feature_cols = ['N_req_kg_per_ha', 'P_req_kg_per_ha', 'K_req_kg_per_ha', 
                    'Temperature_C', 'Humidity_%', 'pH', 'Rainfall_mm']
    
    # Clean data
    df_clean = df.dropna(subset=feature_cols + ['Crop']).copy()
    df_clean['Crop'] = df_clean['Crop'].str.strip().str.lower()
    
    X = df_clean[feature_cols]
    y = df_clean['Crop']
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    clf = RandomForestClassifier(n_estimators=60, max_depth=14, random_state=42, n_jobs=-1)
    clf.fit(X, y_encoded)
    
    model_data = {
        "model": clf,
        "label_encoder": le,
        "feature_names": feature_cols,
        "classes": list(le.classes_),
        "version": "1.0.0"
    }
    
    out_file = MODELS_DIR / "crop_recommender.joblib"
    joblib.dump(model_data, out_file)
    print(f" [OK] Crop Recommender trained & saved to {out_file} (Classes: {list(le.classes_)})")
    return model_data

def train_yield_regressor():
    """
    Trains a Regressor to predict Yield_kg_per_ha:
    Inputs: Crop (encoded), State (encoded), Area_ha, N_req, P_req, K_req, Temp, Humidity, pH, Rainfall
    """
    csv_path = Path(r"C:\Users\raika\Downloads\mynew\Custom_Crops_yield_Historical_Dataset.csv")
    if not csv_path.exists():
        return None
        
    print("-> Loading Custom_Crops_yield_Historical_Dataset for Yield Prediction...")
    df = pd.read_csv(csv_path)
    
    df_clean = df.dropna(subset=[
        'Crop', 'State Name', 'Area_ha', 'Yield_kg_per_ha',
        'N_req_kg_per_ha', 'P_req_kg_per_ha', 'K_req_kg_per_ha',
        'Temperature_C', 'Humidity_%', 'pH', 'Rainfall_mm'
    ]).copy()
    
    df_clean['Crop'] = df_clean['Crop'].str.strip().str.lower()
    df_clean['State Name'] = df_clean['State Name'].str.strip()
    
    crop_le = LabelEncoder()
    state_le = LabelEncoder()
    
    df_clean['crop_code'] = crop_le.fit_transform(df_clean['Crop'])
    df_clean['state_code'] = state_le.fit_transform(df_clean['State Name'])
    
    features = [
        'crop_code', 'state_code', 'Area_ha',
        'N_req_kg_per_ha', 'P_req_kg_per_ha', 'K_req_kg_per_ha',
        'Temperature_C', 'Humidity_%', 'pH', 'Rainfall_mm'
    ]
    
    X = df_clean[features]
    y = df_clean['Yield_kg_per_ha']
    
    reg = RandomForestRegressor(n_estimators=50, max_depth=16, random_state=42, n_jobs=-1)
    reg.fit(X, y)
    
    model_data = {
        "model": reg,
        "crop_encoder": crop_le,
        "state_encoder": state_le,
        "feature_names": features,
        "version": "1.0.0"
    }
    
    out_file = MODELS_DIR / "yield_regressor.joblib"
    joblib.dump(model_data, out_file)
    print(f" [OK] Yield Regressor trained & saved to {out_file}")
    return model_data

def train_resource_optimizer():
    """
    Trains resource efficiency estimator from agriculture_dataset.csv
    Predicts water usage, fertilizer tons, and pesticide kg per acre.
    """
    csv_path = Path(r"C:\Users\raika\Downloads\mynew\agriculture_dataset.csv")
    if not csv_path.exists():
        return None
        
    print("-> Loading agriculture_dataset.csv for Resource Efficiency Modeling...")
    df = pd.read_csv(csv_path)
    
    crop_soil_benchmarks = {}
    for crop, group in df.groupby('Crop_Type'):
        crop_soil_benchmarks[crop.lower()] = {
            "avg_water_m3_per_acre": float((group['Water_Usage(cubic meters)'] / group['Farm_Area(acres)']).mean()),
            "avg_fertilizer_ton_per_acre": float((group['Fertilizer_Used(tons)'] / group['Farm_Area(acres)']).mean()),
            "avg_pesticide_kg_per_acre": float((group['Pesticide_Used(kg)'] / group['Farm_Area(acres)']).mean()),
            "avg_yield_ton_per_acre": float((group['Yield(tons)'] / group['Farm_Area(acres)']).mean()),
            "irrigation_types": group['Irrigation_Type'].unique().tolist(),
            "soil_types": group['Soil_Type'].unique().tolist(),
        }
    
    out_file = MODELS_DIR / "resource_benchmarks.joblib"
    joblib.dump(crop_soil_benchmarks, out_file)
    print(f" [OK] Resource Benchmarks compiled & saved to {out_file} ({len(crop_soil_benchmarks)} crops)")
    return crop_soil_benchmarks

if __name__ == "__main__":
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("=== TRAINING AGRIGO AGRICULTURAL AI MODELS ===")
    train_crop_recommender()
    train_yield_regressor()
    train_resource_optimizer()
    print("=== MODEL TRAINING COMPLETE ===")
