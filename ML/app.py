import os
import json
import pickle
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

# Import ML pipeline predictor from local ML folder
from ml_pipeline import MedicalSDOHInferencePipeline, predict

# Global pipeline instance
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pkl_path = os.path.join(current_dir, "ml_pipeline.pkl")
        if os.path.exists(pkl_path):
            print(f"Loading pre-trained pipeline from {pkl_path}...")
            try:
                with open(pkl_path, "rb") as f:
                    pipeline_instance = pickle.load(f)
                print("Successfully loaded pre-trained pipeline from .pkl!")
            except Exception as e:
                print(f"Error loading .pkl file ({e}), fitting fresh pipeline...")
                pipeline_instance = MedicalSDOHInferencePipeline()
                pipeline_instance.fit()
        else:
            print("Fitting fresh pipeline...")
            pipeline_instance = MedicalSDOHInferencePipeline()
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
def predict_endpoint(payload: PredictRequest = Body(...)):
    """
    POST /predict
    Crash-proof endpoint for multi-label disease prediction (Diabetes, Hypertension, Heart Disease, Asthma).
    Accepts raw OCR patient medical data and frontend-style locations (country, state, county).
    """
    try:
        pipeline = get_pipeline()
        payload_dict = payload.dict()
        output = pipeline.predict(payload_dict)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
