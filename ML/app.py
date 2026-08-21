import os
import json
import pickle
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

from ml_pipelineV2 import MedicalSDOHInferencePipelineV2

# Global pipeline V2 instance
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(current_dir, "ml_pipelineV2.pkl")
        if not os.path.exists(pkl_path):
            # Check parent workspace
            parent_pkl = os.path.join(os.path.dirname(current_dir), "ml_pipelineV2.pkl")
            if os.path.exists(parent_pkl):
                pkl_path = parent_pkl
        if os.path.exists(pkl_path):
            print(f"Loading pre-trained V2 pipeline from {pkl_path}...")
            try:
                with open(pkl_path, "rb") as f:
                    pipeline_instance = pickle.load(f)
                print("Successfully loaded pre-trained ml_pipelineV2.pkl!")
            except Exception as e:
                print(f"Error loading V2 .pkl file ({e}), fitting fresh V2 pipeline...")
                pipeline_instance = MedicalSDOHInferencePipelineV2()
                pipeline_instance.fit()
        else:
            print("Fitting fresh V2 pipeline...")
            pipeline_instance = MedicalSDOHInferencePipelineV2()
            pipeline_instance.fit()
    return pipeline_instance

# Initialize pipeline at module load time
get_pipeline()

# Initialize FastAPI App
app = FastAPI(
    title="Medical & SDOH Disease Prediction API",
    description="Crash-proof API predicting multi-label disease risks (Diabetes, Hypertension, Heart Disease, Asthma) and Top 3 SDOH feature drivers per county.",
    version="1.0.0"
)

# ============================================================
# REQUEST & RESPONSE PYDANTIC SCHEMAS (FRONTEND MATCHING)
# ============================================================

class LocationItem(BaseModel):
    country: Optional[str] = Field(default="USA", example="USA")
    state: Optional[str] = Field(default="AL", example="AL")
    county: Optional[str] = Field(default="Limestone County", example="Limestone County")
    county_fips: Optional[str] = Field(default=None, example=None)

class PredictRequest(BaseModel):
    patient_id: Optional[str] = Field(default="FRONTEND_PATIENT_2026_01", example="FRONTEND_PATIENT_2026_01")
    medical_data: Optional[Dict[str, Any]] = Field(
        default={
            "age": 58,
            "bmi": 32.1,
            "systolic_bp": 142,
            "smoking_status": True
        },
        example={
            "age": 58,
            "bmi": 32.1,
            "systolic_bp": 142,
            "hba1c": 6.8,
            "smoking_status": True
        }
    )
    location: Optional[LocationItem] = None
    locations: Optional[List[LocationItem]] = Field(
        default=[
            {"country": "USA", "state": "AL", "county": "Limestone County"},
            {"country": "USA", "state": "AL", "county": "Wilcox County"}
        ]
    )

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Medical & SDOH Disease Prediction API",
        "endpoints": {
            "predict": "POST /predict",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
def health_check():
    pipeline = get_pipeline()
    return {"status": "healthy", "pipeline_loaded": pipeline is not None}

@app.post("/predict")
def predict_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    POST /predict
    Crash-proof endpoint for multi-label disease prediction (ml_pipelineV2.pkl).
    Accepts raw OCR patient medical data, target_locations list-of-lists [[county, state, country]], and medical conditions.
    Logs input JSON, model processing step, output JSON, and errors directly to docker/terminal logs.
    """
    print("\n" + "="*80, flush=True)
    print("📥 [ML SERVICE] RECEIVED CONSOLIDATED INPUT JSON PAYLOAD:", flush=True)
    print(json.dumps(payload, indent=2), flush=True)
    print("="*80, flush=True)

    try:
        print("⚙️ [ML SERVICE] Initializing ML Model Pipeline (ml_pipelineV2.pkl)...", flush=True)
        pipeline = get_pipeline()
        
        # Handle list of lists locations [[county, state, country], ...]
        locations = []
        if "target_locations" in payload and isinstance(payload["target_locations"], list):
            for loc_item in payload["target_locations"]:
                if isinstance(loc_item, list) and len(loc_item) >= 2:
                    county = loc_item[0]
                    state = loc_item[1]
                    country = loc_item[2] if len(loc_item) > 2 else "United States"
                    locations.append({"county": county, "state": state, "country": country})
                elif isinstance(loc_item, dict):
                    locations.append(loc_item)
        elif "locations" in payload and isinstance(payload["locations"], list):
            for loc_item in payload["locations"]:
                if isinstance(loc_item, list) and len(loc_item) >= 2:
                    locations.append({"county": loc_item[0], "state": loc_item[1], "country": loc_item[2] if len(loc_item) > 2 else "United States"})
                elif isinstance(loc_item, dict):
                    locations.append(loc_item)
                    
        if locations:
            payload["locations"] = locations
            
        print(f"🔄 [ML SERVICE] Processing prediction across {len(locations)} location(s) using ml_pipelineV2.pkl...", flush=True)
        output = pipeline.predict(payload)
        
        print("\n" + "="*80, flush=True)
        print("📤 [ML SERVICE] GENERATED MODEL PREDICTION OUTPUT JSON:", flush=True)
        print(json.dumps(output, indent=2), flush=True)
        print("="*80 + "\n", flush=True)
        
        return output
    except Exception as e:
        error_msg = f"Prediction error: {str(e)}"
        print("\n" + "❌"*40, flush=True)
        print(f"❌ [ML SERVICE ERROR] {error_msg}", flush=True)
        print("❌"*40 + "\n", flush=True)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
