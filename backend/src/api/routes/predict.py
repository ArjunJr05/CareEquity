import os
import pickle
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body

import sys
from .ml_pipelineV2 import MedicalSDOHInferencePipelineV2

# Register ml_pipelineV2 in sys.modules so pickle.load works without error
sys.modules['ml_pipelineV2'] = sys.modules[__name__]
sys.modules['ml_pipelineV2'].MedicalSDOHInferencePipelineV2 = MedicalSDOHInferencePipelineV2

router = APIRouter(
    prefix="",
    tags=["predict"]
)

# Global pipeline V2 instance
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        # Search for ml_pipelineV2.pkl across probable directory locations
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # root or backend root
        workspace_root = os.path.abspath(os.path.join(backend_dir, ".."))
        
        candidate_paths = [
            os.path.join(workspace_root, "ML", "ml_pipelineV2.pkl"),
            os.path.join(workspace_root, "ml_pipelineV2.pkl"),
            os.path.join(backend_dir, "ML", "ml_pipelineV2.pkl"),
            os.path.join(current_dir, "ml_pipelineV2.pkl"),
            r"e:\CareEquity\ML\ml_pipelineV2.pkl",
            r"e:\CareEquity\ml_pipelineV2.pkl"
        ]
        
        pkl_path = None
        for path in candidate_paths:
            if os.path.exists(path):
                pkl_path = path
                break
                
        if pkl_path:
            print(f"Loading pre-trained V2 pipeline from {pkl_path}...")
            try:
                with open(pkl_path, "rb") as f:
                    pipeline_instance = pickle.load(f)
                print("Successfully loaded pre-trained ml_pipelineV2.pkl!")
            except Exception as e:
                print(f"Error loading V2 .pkl file ({e}), trying fallback pipeline...")
        
        if pipeline_instance is None:
            try:
                import sys
                ml_dir = os.path.join(workspace_root, "ML")
                if ml_dir not in sys.path:
                    sys.path.insert(0, ml_dir)
                from ml_pipelineV2 import MedicalSDOHInferencePipelineV2
                print("Fitting fresh V2 pipeline instance...")
                pipeline_instance = MedicalSDOHInferencePipelineV2()
                pipeline_instance.fit()
            except Exception as e:
                print(f"Error initializing fresh MedicalSDOHInferencePipelineV2: {e}")

    return pipeline_instance

@router.post("/predict")
def predict_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    POST /predict
    Crash-proof endpoint for multi-label disease prediction (ml_pipelineV2.pkl).
    Accepts patient medical data, target_locations list [[county, state, country]], and medical conditions.
    """
    try:
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
            
        output = pipeline.predict(payload)
        return output
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
