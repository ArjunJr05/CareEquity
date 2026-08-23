import os
import json
import pickle
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

# Import ML pipeline V3 predictor
try:
    from ML.ml_pipelineV3 import MedicalSDOHInferencePipelineV3, predict
except ImportError:
    from ml_pipelineV3 import MedicalSDOHInferencePipelineV3, predict

# Global pipeline instance
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(current_dir, "ml_pipelineV3.pkl")
        if not os.path.exists(pkl_path):
            pkl_path = os.path.join(os.path.dirname(current_dir), "ml_pipelineV3.pkl")
            
        if os.path.exists(pkl_path):
            print(f"Loading pre-trained V3 pipeline from {pkl_path}...")
            try:
                with open(pkl_path, "rb") as f:
                    pipeline_instance = pickle.load(f)
                print("Successfully loaded pre-trained V3 pipeline from .pkl!")
            except Exception as e:
                print(f"Error loading .pkl file ({e}), fitting fresh V3 pipeline...")
                pipeline_instance = MedicalSDOHInferencePipelineV3()
                pipeline_instance.fit()
        else:
            print("Fitting fresh V3 pipeline...")
            pipeline_instance = MedicalSDOHInferencePipelineV3()
            pipeline_instance.fit()
    return pipeline_instance

# Initialize pipeline at module load time
get_pipeline()

# Initialize FastAPI App
app = FastAPI(
    title="Medical & SDOH Disease Prediction API",
    description="Crash-proof API predicting multi-label disease risks (Diabetes, Hypertension, Heart Disease, Asthma), SDoH feature levels, and County Health Equity Score.",
    version="3.0.0"
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
        "service": "Medical & SDOH Disease Prediction API (V3)",
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
    Crash-proof endpoint for multi-label disease prediction (ml_pipelineV3.pkl).
    Accepts raw OCR patient medical data, target_locations list-of-lists [[county, state, country]], and frontend location objects.
    Logs input JSON, processing step, output JSON, and errors directly to console logs.
    """
    print("\n" + "="*80, flush=True)
    print("📥 [ML SERVICE V3] RECEIVED CONSOLIDATED INPUT JSON PAYLOAD:", flush=True)
    print(json.dumps(payload, indent=2), flush=True)
    print("="*80, flush=True)

    try:
        print("⚙️ [ML SERVICE V3] Initializing ML Model Pipeline (ml_pipelineV3.pkl)...", flush=True)
        pipeline = get_pipeline()
        
        output = pipeline.predict(payload)
        
        print("\n" + "="*80, flush=True)
        print("📤 [ML SERVICE V3] GENERATED MODEL PREDICTION OUTPUT JSON:", flush=True)
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
