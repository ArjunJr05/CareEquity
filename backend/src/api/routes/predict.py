import os
import sys
import pickle
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body

# Dynamically append potential ML directory locations to sys.path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
possible_ml_dirs = [
    os.path.abspath(os.path.join(current_file_dir, "..", "..", "..", "ML")),
    os.path.abspath(os.path.join(current_file_dir, "..", "..", "ML")),
    os.path.abspath(os.path.join(current_file_dir, "..", "ML")),
    "/app/ML",
    "/app"
]
for d in possible_ml_dirs:
    if os.path.exists(d) and d not in sys.path:
        sys.path.insert(0, d)

try:
    from ml_pipelineV3 import MedicalSDOHInferencePipelineV3, predict as ml_v3_predict
except ImportError:
    from ML.ml_pipelineV3 import MedicalSDOHInferencePipelineV3, predict as ml_v3_predict

router = APIRouter(
    prefix="",
    tags=["predict"]
)

pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        print("⚙️ Initializing and fitting fresh MedicalSDOHInferencePipelineV3 instance for dynamic prediction...")
        pipeline_instance = MedicalSDOHInferencePipelineV3()
        try:
            pipeline_instance.fit()
            print("✅ MedicalSDOHInferencePipelineV3 fitted successfully!")
        except Exception as e:
            print(f"Note on fitting pipeline: {e}")

    return pipeline_instance

@router.post("/predict")
def predict_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    POST /predict
    Crash-proof endpoint for multi-label disease prediction (ml_pipelineV2.pkl).
    Accepts patient medical data, target_locations list [[county, state, country]], and medical conditions.
    Prints structured input, processing, output JSON, and errors to logs.
    """
    import json
    print("\n" + "="*80, flush=True)
    print("📥 [MAIN BACKEND] RECEIVED CONSOLIDATED PATIENT & LOCATION INPUT JSON:", flush=True)
    print(json.dumps(payload, indent=2), flush=True)
    print("="*80, flush=True)

    try:
        print("⚙️ [MAIN BACKEND] Initializing ML Pipeline (ml_pipelineV2.pkl)...", flush=True)
        pipeline = get_pipeline()
        if pipeline is None:
            raise HTTPException(status_code=500, detail="ML Pipeline V2 instance unavailable")

        # Normalize locations parameter format
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
            
        print(f"🔄 [MAIN BACKEND] Executing ML Model prediction across {len(locations)} location(s)...", flush=True)
        output = pipeline.predict(payload)
        
        print("\n" + "="*80, flush=True)
        print("📤 [MAIN BACKEND] GENERATED MODEL OUTPUT PREDICTION JSON:", flush=True)
        print(json.dumps(output, indent=2), flush=True)
        print("="*80 + "\n", flush=True)
        
        return output
    except Exception as e:
        error_msg = f"Prediction error: {str(e)}"
        print("\n" + "❌"*40, flush=True)
        print(f"❌ [MAIN BACKEND PREDICT ERROR] {error_msg}", flush=True)
        print("❌"*40 + "\n", flush=True)
        raise HTTPException(status_code=500, detail=error_msg)
