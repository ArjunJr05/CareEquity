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
        # Check for pre-fitted pkl first
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        workspace_dir = os.path.abspath(os.path.join(backend_dir, ".."))
        
        pkl_candidates = [
            os.path.join(workspace_dir, "ML", "ml_pipelineV3.pkl"),
            os.path.join(backend_dir, "ML", "ml_pipelineV3.pkl"),
            "/app/ML/ml_pipelineV3.pkl",
            r"e:\CareEquity\ML\ml_pipelineV3.pkl"
        ]
        
        pkl_path = next((p for p in pkl_candidates if os.path.exists(p)), None)
        if pkl_path:
            try:
                print(f"⚙️ Loading pre-trained ML Pipeline V3 from {pkl_path}...", flush=True)
                with open(pkl_path, "rb") as f:
                    pipeline_instance = pickle.load(f)
                print("✅ ML Pipeline V3 loaded successfully from pkl!", flush=True)
                return pipeline_instance
            except Exception as err:
                print(f"⚠️ Error loading pkl ({err}), falling back to pipeline fitting...", flush=True)

        print("⚙️ Initializing fresh MedicalSDOHInferencePipelineV3 instance for dynamic prediction...", flush=True)
        med_path = os.path.join(workspace_dir, "clinical_data", "synthetic_medical_75000_V2.csv")
        sdoh_path = os.path.join(workspace_dir, "dataset", "synthetic_county_context_50_FINAL.csv")
        pipeline_instance = MedicalSDOHInferencePipelineV3(med_dataset_path=med_path, sdoh_dataset_path=sdoh_path)
        try:
            pipeline_instance.fit()
            print("✅ MedicalSDOHInferencePipelineV3 fitted successfully!", flush=True)
        except Exception as e:
            print(f"Note on fitting pipeline: {e}", flush=True)

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

        # Forward request to standalone ML microservice container if configured
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-backend:8000")
        if ml_service_url:
            try:
                import requests
                print(f"📡 Forwarding prediction request to ML Container at {ml_service_url}/predict...", flush=True)
                resp = requests.post(f"{ml_service_url.rstrip('/')}/predict", json=payload, timeout=30)
                if resp.status_code == 200:
                    output = resp.json()
                    print("\n" + "="*80, flush=True)
                    print("📤 [MAIN BACKEND] GENERATED MODEL OUTPUT PREDICTION JSON (Via ML Service):", flush=True)
                    print(json.dumps(output, indent=2), flush=True)
                    print("="*80 + "\n", flush=True)
                    return output
                else:
                    print(f"⚠️ ML Service container returned status {resp.status_code}, falling back to local pipeline...", flush=True)
            except Exception as net_err:
                print(f"⚠️ Could not reach ML container ({net_err}), executing via local pipeline instance...", flush=True)

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
