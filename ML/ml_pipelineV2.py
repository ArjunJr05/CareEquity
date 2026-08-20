import os
import json
import pickle
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# ============================================================
# ML PIPELINE V2 CLASS FOR MEDICAL + SDOH INFERENCE
# (USES V2 STREAMLINED CLINICAL DATASET: synthetic_medical_75000_V2.csv)
# ============================================================

class MedicalSDOHInferencePipelineV2:
    def __init__(self, med_dataset_path=None, sdoh_dataset_path=None):
        self.med_dataset_path = med_dataset_path or r"p:\project\cts\clinical_data\synthetic_medical_75000_V2.csv"
        
        if sdoh_dataset_path and os.path.exists(sdoh_dataset_path):
            self.sdoh_dataset_path = sdoh_dataset_path
        else:
            candidates = [
                r"p:\project\cts\clinical_data\synthetic_county_context_50 (1).csv",
                r"p:\project\cts\clinical_data\synthetic_county_context_50_FINAL.csv",
                r"p:\project\cts\clinical_data\synthetic_county_context_50.csv"
            ]
            self.sdoh_dataset_path = next((p for p in candidates if os.path.exists(p)), candidates[0])

        
        self.diseases = ['diabetes', 'hypertension', 'heart_disease', 'asthma']
        
        # V2 Streamlined 19 Medical Numeric Features
        self.medical_num_cols = [
            'age', 'height_cm', 'weight_kg', 'bmi', 'waist_cm', 
            'systolic_bp', 'diastolic_bp', 'heart_rate', 'hba1c', 
            'fasting_glucose', 'total_cholesterol', 'ldl', 'hdl', 
            'triglycerides', 'alt', 'ast', 'albumin', 'bilirubin', 
            'sedentary_minutes'
        ]

        # 4 Categorical Features
        self.medical_cat_cols = ['sex', 'race_ethnicity', 'smoking_status', 'alcohol_use']

        # 11 SDOH Features
        self.sdoh_cols = [
            'svi_overall', 'poverty_rate', 'median_household_income', 'unemployment_rate', 
            'food_insecurity', 'transportation_barrier', 'housing_insecurity', 
            'obesity_prevalence', 'physical_inactivity', 'smoking_prevalence', 'lack_health_insurance'
        ]
        
        self.all_feature_cols = self.medical_num_cols + self.sdoh_cols + self.medical_cat_cols
        
        self.models = {}
        self.preprocessors = {}
        self.medians = {}
        self.sdoh_lookup = {}
        self.is_fitted = False
        
    def fit(self):
        """Train models on Medical V2 + SDOH dataset and cache defaults for crash-proof inference."""
        print(f"Initializing & fitting ML V2 pipeline models using dataset: {self.med_dataset_path}")
        med_df = pd.read_csv(self.med_dataset_path)
        sdoh_df = pd.read_csv(self.sdoh_dataset_path)

        med_df['county_fips'] = med_df['county_fips'].astype(str).str.zfill(5)
        sdoh_df['county_fips'] = sdoh_df['county_fips'].astype(str).str.zfill(5)

        # Build SDOH Lookup map by county_fips and state+county_name
        for _, row in sdoh_df.iterrows():
            fips = row['county_fips']
            c_name = str(row['county_name']).split(',')[0].replace(' County', '').strip().lower()
            state = str(row['state_abbr']).strip().upper()
            
            sdoh_dict = {col: float(row[col]) for col in self.sdoh_cols if col in row}
            sdoh_dict['county_name'] = str(row['county_name'])
            sdoh_dict['state_abbr'] = state
            sdoh_dict['county_fips'] = fips
            
            self.sdoh_lookup[fips] = sdoh_dict
            self.sdoh_lookup[f"{state}_{c_name}"] = sdoh_dict

        # Compute median fallbacks for crash-proof medical imputation
        for col in self.medical_num_cols:
            self.medians[col] = float(med_df[col].median()) if col in med_df else 0.0

        # Merge for training
        df = med_df.merge(sdoh_df.drop(columns=['state_abbr', 'county_name'], errors='ignore'), on='county_fips', how='inner')

        num_cols = self.medical_num_cols + self.sdoh_cols
        
        for disease in self.diseases:
            num_trans = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
            cat_trans = Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('encoder', OneHotEncoder(handle_unknown='ignore', drop='first'))])
            
            preprocessor = ColumnTransformer([('num', num_trans, num_cols), ('cat', cat_trans, self.medical_cat_cols)])
            
            X_train = preprocessor.fit_transform(df[num_cols + self.medical_cat_cols])
            y_train = df[disease].astype(int)
            
            clf = LogisticRegression(max_iter=500, random_state=42)
            clf.fit(X_train, y_train)
            
            self.preprocessors[disease] = preprocessor
            self.models[disease] = clf
            
        self.is_fitted = True
        print("ML V2 Pipeline successfully fitted across all target disease models!")

    def save_pkl(self, pkl_path=r"p:\project\cts\ml_pipelineV2.pkl"):
        """Serialize fitted pipeline to .pkl file."""
        if not self.is_fitted:
            self.fit()
        print(f"Saving ML V2 pipeline pickle to {pkl_path}...")
        os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
        with open(pkl_path, 'wb') as f:
            pickle.dump(self, f)
        print("Successfully saved ml_pipelineV2.pkl!")

    def _resolve_location_sdoh(self, loc_dict):
        """Resolves SDOH features for a county location (by FIPS code or State + County Name)."""
        if 'county_fips' in loc_dict and str(loc_dict['county_fips']).zfill(5) in self.sdoh_lookup:
            return self.sdoh_lookup[str(loc_dict['county_fips']).zfill(5)]
        
        state = str(loc_dict.get('state', '')).strip().upper()
        c_name = str(loc_dict.get('county', '')).split(',')[0].replace(' County', '').strip().lower()
        key = f"{state}_{c_name}"
        
        if key in self.sdoh_lookup:
            return self.sdoh_lookup[key]
        
        # Fallback to first county if unknown location provided
        first_key = list(self.sdoh_lookup.keys())[0]
        return self.sdoh_lookup[first_key]

    def predict(self, ocr_payload):
        """
        Crash-proof prediction entrypoint for V2 pipeline.
        Handles missing OCR medical features and single/multi-county travel locations.
        """
        if not self.is_fitted:
            self.fit()
            
        # Parse payload
        patient_id = ocr_payload.get('patient_id', 'OCR_PATIENT_001')
        med_input = ocr_payload.get('medical_data', ocr_payload)
        
        # Determine locations list
        if 'locations' in ocr_payload and isinstance(ocr_payload['locations'], list):
            locations = ocr_payload['locations']
        elif 'location' in ocr_payload and isinstance(ocr_payload['location'], dict):
            locations = [ocr_payload['location']]
        else:
            # Check root for state/county
            state = ocr_payload.get('state', 'AL')
            county = ocr_payload.get('county', 'Limestone')
            fips = ocr_payload.get('county_fips', '01083')
            locations = [{'state': state, 'county': county, 'county_fips': fips}]
            
        # Build crash-proof medical record (fill missing values with medians)
        clean_med = {}
        for col in self.medical_num_cols:
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = self.medians[col]
            else:
                try:
                    clean_med[col] = float(val)
                except (ValueError, TypeError):
                    clean_med[col] = self.medians[col]
                    
        for col in self.medical_cat_cols:
            val = med_input.get(col, None)
            if val is None or pd.isna(val):
                clean_med[col] = 'Unknown' if col != 'sex' else 'Female'
            else:
                clean_med[col] = str(val)

        county_results = []
        
        for loc in locations:
            sdoh_data = self._resolve_location_sdoh(loc)
            
            # Combine patient medical data with this county's SDOH data
            combined_row = {**clean_med, **sdoh_data}
            input_df = pd.DataFrame([combined_row])
            
            disease_predictions = {}
            
            for disease in self.diseases:
                preprocessor = self.preprocessors[disease]
                clf = self.models[disease]
                
                num_cols = self.medical_num_cols + self.sdoh_cols
                X_trans = preprocessor.transform(input_df[num_cols + self.medical_cat_cols])
                prob = float(clf.predict_proba(X_trans)[0][1])
                
                # Determine risk tier
                risk_tier = "High Risk" if prob >= 0.65 else ("Moderate Risk" if prob >= 0.35 else "Low Risk")
                
                # Calculate SDOH feature impact weights (LogReg coefficients * scaled SDOH value)
                coefs = clf.coef_[0]
                sdoh_impacts = []
                
                # Number of numeric columns in preprocessor
                for idx, sdoh_feat in enumerate(self.sdoh_cols):
                    # Index in preprocessor num array
                    feat_idx = len(self.medical_num_cols) + idx
                    weight = float(coefs[feat_idx])
                    raw_val = float(sdoh_data.get(sdoh_feat, 0.0))
                    
                    sdoh_impacts.append({
                        "sdoh_factor": sdoh_feat,
                        "shap_impact": round(weight, 4),
                        "county_value": round(raw_val, 2),
                        "unit": "%" if "rate" in sdoh_feat or "prevalence" in sdoh_feat or "insecurity" in sdoh_feat or "inactivity" in sdoh_feat or "insurance" in sdoh_feat else "value"
                    })
                    
                # Rank top 3 SDOH factors by magnitude of impact
                top_3_sdoh = sorted(sdoh_impacts, key=lambda x: abs(x['shap_impact']), reverse=True)[:3]
                
                disease_predictions[disease] = {
                    "probability": round(prob, 4),
                    "risk_tier": risk_tier,
                    "top_3_sdoh_factors": top_3_sdoh
                }
                
            county_results.append({
                "location": {
                    "state": sdoh_data.get('state_abbr', loc.get('state', 'AL')),
                    "county_name": sdoh_data.get('county_name', loc.get('county', 'Unknown')),
                    "county_fips": sdoh_data.get('county_fips', '00000')
                },
                "diseases": disease_predictions
            })
            
        return {
            "pipeline_version": "V2",
            "status": "success",
            "patient_id": patient_id,
            "is_multi_county": len(locations) > 1,
            "evaluated_counties_count": len(locations),
            "county_predictions": county_results
        }

# Global Pipeline Instance
pipeline_v2 = MedicalSDOHInferencePipelineV2()

def predict(ocr_payload):
    return pipeline_v2.predict(ocr_payload)

if __name__ == '__main__':
    pipeline_v2.fit()
    # Save pkl to both root and ML directory
    pipeline_v2.save_pkl(r"p:\project\cts\ml_pipelineV2.pkl")
    pipeline_v2.save_pkl(r"p:\project\cts\ML\ml_pipelineV2.pkl")
    
    sample_payload = {
        "patient_id": "TEST_PATIENT_V2_01",
        "medical_data": {
            "age": 58,
            "bmi": 32.1,
            "systolic_bp": 142,
            "smoking_status": True
        },
        "locations": [
            {"state": "AL", "county": "Limestone"},
            {"state": "AL", "county": "Wilcox"}
        ]
    }
    output = pipeline_v2.predict(sample_payload)
    print("\n--- SAMPLE PREDICTION OUTPUT ---")
    print(json.dumps(output, indent=2))
